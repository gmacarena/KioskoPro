import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
import datetime
import os
import logging
from repos import ProductoRepo, VentaRepo, PuntoVentaRepo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NuevaVentaPro")

CURRENCY_QUANTIZE = Decimal('0.01')

def money(v) -> str:
    try:
        d = Decimal(v).quantize(CURRENCY_QUANTIZE, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError):
        d = Decimal('0.00')
    return f"${d:,.2f}"

@dataclass
class VentaItem:
    producto_id: int
    codigo_barras: str
    nombre: str
    precio: Decimal
    cantidad: int = 1
    stock: int = 0

    def __post_init__(self):
        if self.cantidad < 0:
            self.cantidad = 0

    @property
    def subtotal(self) -> Decimal:
        return (self.precio * Decimal(self.cantidad)).quantize(CURRENCY_QUANTIZE, rounding=ROUND_HALF_UP)
    
    @property
    def tiene_stock(self) -> bool:
        return self.stock >= self.cantidad
    
    @property
    def stock_disponible(self) -> int:
        """Stock disponible para vender (no puede ser negativo)"""
        return max(0, self.stock)
    
    def puede_vender(self, cantidad=None) -> bool:
        """Verificar si se puede vender la cantidad especificada"""
        if cantidad is None:
            cantidad = self.cantidad
        return self.stock >= cantidad and cantidad > 0

class PagoDialog(tk.Toplevel):
    """Diálogo para procesar el pago de la venta"""
    
    def __init__(self, parent, total: Decimal):
        super().__init__(parent)
        self.parent = parent
        self.total = total
        self.resultado = None
        
        self.title("💳 PROCESAR PAGO")
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self._construir_ui()
        
    def _construir_ui(self):
        """Construir interfaz del diálogo de pago"""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Total a pagar
        ttk.Label(main_frame, text="TOTAL A PAGAR:", 
                 font=("Segoe UI", 16, "bold")).pack(pady=(0, 10))
        ttk.Label(main_frame, text=money(self.total), 
                 font=("Segoe UI", 24, "bold"), foreground="#27ae60").pack(pady=(0, 20))
        
        # Forma de pago
        pago_frame = ttk.LabelFrame(main_frame, text="FORMA DE PAGO", padding="10")
        pago_frame.pack(fill="x", pady=10)
        
        self.forma_pago = tk.StringVar(value="EFECTIVO")
        
        ttk.Radiobutton(pago_frame, text="💰 Efectivo", 
                       variable=self.forma_pago, value="EFECTIVO").pack(anchor="w")
        ttk.Radiobutton(pago_frame, text="💳 Tarjeta Débito", 
                       variable=self.forma_pago, value="TARJETA_DEBITO").pack(anchor="w")
        ttk.Radiobutton(pago_frame, text="💳 Tarjeta Crédito", 
                       variable=self.forma_pago, value="TARJETA_CREDITO").pack(anchor="w")
        ttk.Radiobutton(pago_frame, text="📱 Transferencia", 
                       variable=self.forma_pago, value="TRANSFERENCIA").pack(anchor="w")
        
        # Monto recibido (solo para efectivo)
        self.monto_frame = ttk.Frame(main_frame)
        self.monto_frame.pack(fill="x", pady=10)
        
        ttk.Label(self.monto_frame, text="Monto Recibido:").pack(side="left")
        self.entry_monto = ttk.Entry(self.monto_frame, width=15, font=("Segoe UI", 12))
        self.entry_monto.pack(side="left", padx=5)
        self.entry_monto.bind("<KeyRelease>", self._calcular_vuelto)
        
        # Vuelto
        self.lbl_vuelto = ttk.Label(main_frame, text="Vuelto: $0.00", 
                                   font=("Segoe UI", 12, "bold"), foreground="#e74c3c")
        self.lbl_vuelto.pack(pady=5)
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=20)
        
        ttk.Button(btn_frame, text="✅ CONFIRMAR PAGO", 
                  command=self._confirmar_pago, style="Accent.TButton").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", 
                  command=self.destroy).pack(side="right", padx=5)
        
        self.entry_monto.focus()
        self.forma_pago.trace('w', self._on_forma_pago_change)
        
    def _on_forma_pago_change(self, *args):
        """Mostrar/ocultar campo de monto según forma de pago"""
        if self.forma_pago.get() == "EFECTIVO":
            self.monto_frame.pack(fill="x", pady=10)
            self.lbl_vuelto.pack(pady=5)
            self.entry_monto.focus()
        else:
            self.monto_frame.pack_forget()
            self.lbl_vuelto.pack_forget()
            
    def _calcular_vuelto(self, event=None):
        """Calcular y mostrar vuelto"""
        try:
            monto_recibido = Decimal(self.entry_monto.get() or "0")
            vuelto = monto_recibido - self.total
            if vuelto >= 0:
                self.lbl_vuelto.config(text=f"Vuelto: {money(vuelto)}", 
                                      foreground="#27ae60")
            else:
                self.lbl_vuelto.config(text=f"Faltante: {money(-vuelto)}", 
                                      foreground="#e74c3c")
        except InvalidOperation:
            self.lbl_vuelto.config(text="Vuelto: $0.00", foreground="#e74c3c")
            
    def _confirmar_pago(self):
        """Confirmar el pago"""
        forma_pago = self.forma_pago.get()
        
        if forma_pago == "EFECTIVO":
            try:
                monto_recibido = Decimal(self.entry_monto.get() or "0")
                if monto_recibido < self.total:
                    messagebox.showwarning("Pago Insuficiente", 
                                         f"El monto recibido (${monto_recibido:.2f}) es menor al total (${self.total:.2f})")
                    return
                    
                self.resultado = {
                    "forma_pago": forma_pago,
                    "monto_recibido": float(monto_recibido),
                    "vuelto": float(monto_recibido - self.total)
                }
                self.destroy()
                
            except InvalidOperation:
                messagebox.showerror("Error", "Monto recibido no válido")
                return
        else:
            self.resultado = {
                "forma_pago": forma_pago,
                "monto_recibido": float(self.total),
                "vuelto": 0.0
            }
            self.destroy()

class AutoCompleteEntry(ttk.Entry):
    def __init__(self, parent, suggestions_callback, on_select_callback, **kwargs):
        super().__init__(parent, **kwargs)
        self.suggestions_callback = suggestions_callback
        self.on_select_callback = on_select_callback
        self.listbox = None
        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<FocusOut>', self._on_focus_out)
        self.bind('<Down>', self._on_down)
        self.bind('<Up>', self._on_up)
        self.bind('<Return>', self._on_return)
        self.bind('<Escape>', self._on_escape)

    def _on_keyrelease(self, event):
        if event.keysym in ['Down', 'Up', 'Return', 'Escape']:
            return
        
        self._show_suggestions()

    def _show_suggestions(self):
        query = self.get().strip()
        if not query or len(query) < 2:
            self._hide_listbox()
            return

        suggestions = self.suggestions_callback(query)
        if not suggestions:
            self._hide_listbox()
            return

        self._create_listbox()
        self.listbox.delete(0, tk.END)
        
        for prod in suggestions[:8]:
            display_text = f"{prod.get('codigo_barras', '')} - {prod['nombre']} - ${float(prod['precio']):.2f}"
            self.listbox.insert(tk.END, display_text)
            self.listbox.data.append(prod)

    def _create_listbox(self):
        if self.listbox:
            self.listbox.destroy()
            
        x = self.winfo_x()
        y = self.winfo_y() + self.winfo_height()
        width = self.winfo_width()
        
        self.listbox = tk.Listbox(self.master, width=width, height=6, 
                                 font=("Segoe UI", 9), bg="white", relief="solid", border=1)
        self.listbox.place(x=x, y=y)
        self.listbox.data = []
        
        self.listbox.bind('<Double-Button-1>', self._on_listbox_select)
        self.listbox.bind('<Return>', self._on_listbox_select)

    def _hide_listbox(self):
        if self.listbox:
            self.listbox.destroy()
            self.listbox = None

    def _on_focus_out(self, event):
        self.after(150, self._hide_listbox)

    def _on_down(self, event):
        if self.listbox and self.listbox.winfo_ismapped():
            self.listbox.focus_set()
            if self.listbox.size() > 0:
                self.listbox.selection_set(0)
            return "break"

    def _on_up(self, event):
        if self.listbox and self.listbox.winfo_ismapped():
            self.listbox.focus_set()
            if self.listbox.size() > 0:
                self.listbox.selection_set(tk.END)
            return "break"

    def _on_return(self, event):
        if self.listbox and self.listbox.winfo_ismapped() and self.listbox.curselection():
            self._on_listbox_select(event)
            return "break"
        else:
            self.master.focus_set()
            self.master._add_from_entry()

    def _on_escape(self, event):
        self._hide_listbox()

    def _on_listbox_select(self, event):
        if not self.listbox or not self.listbox.curselection():
            return
            
        index = self.listbox.curselection()[0]
        if index < len(self.listbox.data):
            product_data = self.listbox.data[index]
            self.on_select_callback(product_data)
            self.delete(0, tk.END)
            self._hide_listbox()

class NuevaVentaFrame(ttk.Frame):
    """Frame SUPER PROFESIONAL para gestión de ventas optimizado para lector de barras"""
    
    FONT_BOLD = ("Segoe UI", 10, "bold")
    FONT_NORMAL = ("Segoe UI", 10)
    FONT_LARGE = ("Segoe UI", 12, "bold")
    COLOR_PRIMARY = "#2c3e50"
    COLOR_SECONDARY = "#3498db"
    COLOR_SUCCESS = "#27ae60"
    COLOR_WARNING = "#e74c3c"

    def __init__(self, master: Optional[tk.Misc] = None) -> None:
        super().__init__(master)
        self.items: List[VentaItem] = []
        self.punto_venta_id = self._obtener_punto_venta()
        self._setup_advanced_style()
        self._build_professional_ui()
        self._bind_advanced_shortcuts()
        
        self.lector_activo = True
        self.buffer_lector = ""
        self.bind('<Key>', self._capturar_lector_barras)

    def _capturar_lector_barras(self, event):
        """Capturar entrada del lector de código de barras"""
        if not self.lector_activo:
            return
            
        if event.char and event.char.isprintable():
            self.buffer_lector += event.char
            
        if event.keysym == 'Return' and self.buffer_lector:
            codigo = self.buffer_lector.strip()
            self.buffer_lector = ""
            if len(codigo) >= 3:  # Mínimo 3 caracteres para código
                self._procesar_codigo_barras(codigo)

    def _obtener_punto_venta(self) -> int:
        """Obtener el ID del punto de venta para esta PC cliente"""
        try:
            puntos = PuntoVentaRepo.listar()
            if not puntos:
                messagebox.showerror("Error", "No hay puntos de venta configurados. Contacte al administrador.")
                return 1
                
            for punto in puntos:
                if 'cliente' in punto['nombre'].lower() or 'pc' in punto['nombre'].lower():
                    return punto['id']
                    
            return puntos[0]['id']
            
        except Exception as e:
            logger.error(f"Error obteniendo punto de venta: {e}")
            messagebox.showerror("Error", f"No se pudo obtener el punto de venta: {e}")
            return 1

    def _setup_advanced_style(self) -> None:
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except Exception:
            pass
        
        s.configure("Professional.TFrame", background="#ecf0f1")
        s.configure("Header.TLabel", font=("Segoe UI", 11, "bold"), foreground=self.COLOR_PRIMARY)
        s.configure("Total.TLabel", font=("Segoe UI", 12, "bold"), foreground=self.COLOR_SUCCESS)
        s.configure("Accent.TButton", background=self.COLOR_SECONDARY, foreground="white")
        
        s.configure("Treeview", font=self.FONT_NORMAL, rowheight=28, borderwidth=0)
        s.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), 
                   background=self.COLOR_PRIMARY, foreground="white", relief="flat")
        
        s.map("Treeview", background=[("selected", self.COLOR_SECONDARY)],
              foreground=[("selected", "white")])

    def _build_professional_ui(self) -> None:
        # === Scrollable container principal ===
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=0, pady=0)

        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0, bg="#ecf0f1")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

        # Frame interno que contendrá todo el contenido de la venta
        scrollable_frame = ttk.Frame(canvas, style="Professional.TFrame")

        # Crear ventana dentro del canvas sin margen extra y sincronizar anchos
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="frame_window")

        def _update_canvas_width(event):
            canvas.itemconfig("frame_window", width=event.width)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", _update_canvas_width)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        main_container = scrollable_frame  # reutilizamos el nombre original



        top_section = ttk.LabelFrame(main_container, text="⚡ ENTRADA RÁPIDA - LECTOR CÓDIGOS DE BARRAS", 
                                   padding=(15, 10), style="Professional.TFrame")
        top_section.pack(fill="x", padx=8, pady=(8, 4))

        input_row = ttk.Frame(top_section)
        input_row.pack(fill="x", pady=5)

        ttk.Label(input_row, text="Código/Nombre:", font=self.FONT_BOLD).pack(side="left", padx=(0, 8))
        
        self.entry_codigo = AutoCompleteEntry(
            input_row, 
            suggestions_callback=self._get_suggestions,
            on_select_callback=self._on_suggestion_selected,
            width=45,
            font=self.FONT_NORMAL
        )
        self.entry_codigo.pack(side="left", padx=8, fill="x", expand=True)
        
        btn_frame = ttk.Frame(input_row)
        btn_frame.pack(side="left", padx=10)
        
        ttk.Button(btn_frame, text="🔍 Buscar Productos (F2)", 
                  command=self._show_busqueda_avanzada).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="📋 Lista Productos (F3)", 
                  command=self._show_lista_productos).pack(side="left", padx=2)

        lector_frame = ttk.Frame(top_section)
        lector_frame.pack(fill="x", pady=5)
        
        self.lector_status = ttk.Label(lector_frame, text="✅ LECTOR ACTIVO - Escanee códigos de barras", 
                                      foreground=self.COLOR_SUCCESS, font=("Segoe UI", 9, "bold"))
        self.lector_status.pack(side="left")
        
        ttk.Button(lector_frame, text="⏸️ Pausar Lector", 
                  command=self._toggle_lector, width=12).pack(side="right", padx=5)

        middle_section = ttk.Frame(main_container)
        middle_section.pack(fill="both", expand=True, padx=8, pady=8)

        tree_frame = ttk.Frame(middle_section)
        tree_frame.pack(fill="both", expand=True)

        columns = ("codigo", "producto", "cantidad", "precio", "subtotal", "stock")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=14)
        
        column_config = [
            ("codigo", "Código", 120),
            ("producto", "Producto", 280),
            ("cantidad", "Cant.", 80),
            ("precio", "Precio Unit.", 100),
            ("subtotal", "Subtotal", 120),
            ("stock", "Stock", 80)
        ]
        
        for col, text, width in column_config:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center")

        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.tag_configure("even", background="#f8f9fa")
        self.tree.tag_configure("odd", background="#ffffff")
        self.tree.tag_configure("sin_stock", background="#ffe6e6", foreground="#cc0000")

        bottom_section = ttk.Frame(main_container)
        bottom_section.pack(fill="x", padx=8, pady=(4, 8))

        totals_panel = ttk.LabelFrame(bottom_section, text="💰 TOTALES", padding=(15, 10))
        totals_panel.pack(side="left", fill="x", expand=True)

        totals_grid = ttk.Frame(totals_panel)
        totals_grid.pack(fill="x")

        self.lbl_items = ttk.Label(totals_grid, text="Items: 0", font=self.FONT_BOLD)
        self.lbl_items.grid(row=0, column=0, padx=20, pady=2, sticky="w")
        
        self.lbl_subtotal = ttk.Label(totals_grid, text="Subtotal: $0.00", font=self.FONT_BOLD)
        self.lbl_subtotal.grid(row=0, column=1, padx=20, pady=2, sticky="w")
        
        self.lbl_total = ttk.Label(totals_grid, text="TOTAL: $0.00", font=self.FONT_LARGE, 
                                 foreground=self.COLOR_SUCCESS)
        self.lbl_total.grid(row=0, column=2, padx=20, pady=2, sticky="w")

        actions_panel = ttk.Frame(bottom_section)
        actions_panel.pack(side="right")

        action_buttons = [
            ("🗑 Eliminar (Del)", self._eliminar_seleccionado, self.COLOR_WARNING),
            ("➕ Agregar (Insert)", self._show_busqueda_avanzada, self.COLOR_SECONDARY),
            ("🧾 Finalizar (F12)", self._finalizar_venta, self.COLOR_SUCCESS),
            ("🔄 Limpiar (F11)", self._limpiar_venta, "#95a5a6")
        ]

        for text, command, color in action_buttons:
            btn = ttk.Button(actions_panel, text=text, command=command, width=16)
            btn.pack(side="left", padx=3)

        self.status_bar = ttk.Label(main_container, text="Listo - Escanee productos o use F2 para búsqueda manual", 
                                  relief="sunken", anchor="w", font=("Segoe UI", 9))
        self.status_bar.pack(fill="x", padx=8, pady=(0, 4))

        self._setup_context_menu()
        self._actualizar_totales()
        self.entry_codigo.focus()

    def _setup_context_menu(self):
        """Configurar menú contextual avanzado"""
        self.context_menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 9))
        self.context_menu.add_command(label="✏️ Editar cantidad", command=self._menu_editar_cantidad)
        self.context_menu.add_command(label="➖ Disminuir 1", command=self._menu_disminuir_1)
        self.context_menu.add_command(label="➕ Aumentar 1", command=self._menu_aumentar_1)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Eliminar ítem", command=self._menu_eliminar_item)
        self.context_menu.add_command(label="📊 Ver información", command=self._menu_ver_info)

        self.tree.bind("<Double-1>", self._on_doble_clic)
        self.tree.bind("<Button-3>", self._on_clic_derecho)
        self.tree.bind("<Delete>", lambda e: self._eliminar_seleccionado())

    def _bind_advanced_shortcuts(self):
        """Configurar atajos de teclado avanzados"""
        shortcuts = [
            ('<F2>', lambda e: self._show_busqueda_avanzada()),
            ('<F3>', lambda e: self._show_lista_productos()),
            ('<F5>', lambda e: self._actualizar_lista_productos()),
            ('<F11>', lambda e: self._limpiar_venta()),
            ('<F12>', lambda e: self._finalizar_venta()),
            ('<Insert>', lambda e: self._show_busqueda_avanzada()),
            ('<Delete>', lambda e: self._eliminar_seleccionado()),
            ('<Control-plus>', lambda e: self._menu_aumentar_1()),
            ('<Control-minus>', lambda e: self._menu_disminuir_1()),
            ('<Control-e>', lambda e: self._menu_editar_cantidad()),
        ]
        
        for key, func in shortcuts:
            self.bind_all(key, func)

    def _get_suggestions(self, query: str) -> List[Dict]:
        """Obtener sugerencias para autocompletado - SOLO PRODUCTOS ACTIVOS"""
        try:
            if not query or len(query) < 2:
                return []
                
            productos = ProductoRepo.listar()
            query_lower = query.lower()
            
            resultados = []
            for prod in productos:
                if prod.get('activo', True) and (query_lower in prod['nombre'].lower() or 
                    query_lower in prod.get('codigo_barras', '').lower()):
                    resultados.append(prod)
                    
            return resultados[:10]
            
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []

    def _procesar_entrada_producto(self, entrada: str):
        """Procesar entrada de producto (código o nombre) - VERIFICAR ACTIVO"""
        try:
            producto = ProductoRepo.buscar(entrada)
            if not producto:
                self._actualizar_status(f"Producto no encontrado: {entrada}")
                messagebox.showwarning("No encontrado", f"No se encontró el producto: {entrada}")
                return
            
            if not producto.get('activo', True):
                self._actualizar_status(f"Producto inactivo: {producto['nombre']}")
                messagebox.showwarning("Producto Inactivo", 
                                    f"El producto '{producto['nombre']}' está inactivo y no se puede vender")
                return
                    
            item = VentaItem(
                producto_id=producto['id'],
                codigo_barras=producto.get('codigo_barras', ''),
                nombre=producto['nombre'],
                precio=Decimal(str(producto['precio'])),
                cantidad=1,
                stock=producto.get('stock', 0)
            )
            
            self._agregar_item(item)
            
        except Exception as e:
            logger.error(f"Error procesando entrada: {e}")
            messagebox.showerror("Error", f"Error al procesar producto: {e}")

    def _procesar_codigo_barras(self, codigo: str):
        """Procesar código de barras escaneado - VERIFICAR ACTIVO"""
        if not self.lector_activo:
            return
            
        try:
            producto = ProductoRepo.buscar(codigo)
            if producto and producto.get('codigo_barras') == codigo:
                if not producto.get('activo', True):
                    self._actualizar_status(f"Producto inactivo: {producto['nombre']}")
                    messagebox.showwarning("Producto Inactivo", 
                                        f"El producto '{producto['nombre']}' está inactivo")
                    return
                    
                self._agregar_producto_desde_datos(producto, 1)
                self._actualizar_status(f"Escaneado: {producto['nombre']}")
            else:
                self._actualizar_status(f"Código no encontrado: {codigo}")
                messagebox.showwarning("Código inválido", f"No se encontró producto para código: {codigo}")
                
        except Exception as e:
            logger.error(f"Error procesando código de barras: {e}")
            messagebox.showerror("Error", f"Error al procesar código: {e}")

    def _on_suggestion_selected(self, product_data: Dict):
        """Cuando se selecciona una sugerencia del autocompletado"""
        try:
            self._agregar_producto_desde_datos(product_data)
            self._actualizar_status(f"Producto agregado: {product_data['nombre']}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar el producto: {e}")

    def _agregar_producto_desde_datos(self, product_data: Dict, cantidad: int = 1):
        """Agregar producto a la venta desde datos del producto"""
        try:
            item = VentaItem(
                producto_id=product_data['id'],
                codigo_barras=product_data.get('codigo_barras', ''),
                nombre=product_data['nombre'],
                precio=Decimal(str(product_data['precio'])),
                cantidad=cantidad,
                stock=product_data.get('stock', 0)
            )
            
            self._agregar_item(item)
            
        except Exception as e:
            logger.error(f"Error agregando producto: {e}")
            raise

    def _agregar_item(self, item: VentaItem):
        """Agregar o actualizar item en la venta"""
        for existing_item in self.items:
            if existing_item.producto_id == item.producto_id:
                existing_item.cantidad += item.cantidad
                self._actualizar_treeview()
                self._actualizar_totales()
                self._actualizar_status(f"Cantidad actualizada: {existing_item.nombre}")
                return
        
        self.items.append(item)
        self._actualizar_treeview()
        self._actualizar_totales()
        self._actualizar_status(f"Agregado: {item.nombre}")

    def _actualizar_treeview(self):
        """Actualizar completamente el treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for idx, item in enumerate(self.items):
            tags = ('even',) if idx % 2 == 0 else ('odd',)
            if not item.tiene_stock:
                tags += ('sin_stock',)
                
            values = (
                item.codigo_barras,
                item.nombre,
                item.cantidad,
                money(item.precio),
                money(item.subtotal),
                item.stock
            )
            
            self.tree.insert('', tk.END, values=values, tags=tags)

    def _actualizar_totales(self):
        """Actualizar display de totales"""
        total_items = sum(item.cantidad for item in self.items)
        subtotal = sum(float(item.subtotal) for item in self.items)
        total = subtotal
        
        self.lbl_items.config(text=f"Items: {total_items}")
        self.lbl_subtotal.config(text=f"Subtotal: ${subtotal:,.2f}")
        self.lbl_total.config(text=f"TOTAL: ${total:,.2f}")

    def _actualizar_status(self, mensaje: str):
        """Actualizar barra de estado"""
        self.status_bar.config(text=mensaje)
        self.after(3000, lambda: self.status_bar.config(text="Listo - Escanee productos o use F2 para búsqueda manual"))

    def _add_from_entry(self):
        """Procesar entrada desde el campo principal (para Enter)"""
        codigo = self.entry_codigo.get().strip()
        if not codigo:
            return
            
        self._procesar_entrada_producto(codigo)
        self.entry_codigo.delete(0, tk.END)

    def _toggle_lector(self):
        """Activar/desactivar modo lector"""
        self.lector_activo = not self.lector_activo
        if self.lector_activo:
            self.lector_status.config(text="✅ LECTOR ACTIVO - Escanee códigos de barras", 
                                    foreground=self.COLOR_SUCCESS)
            self.entry_codigo.focus()
            self._actualizar_status("Lector activado - Listo para escanear")
        else:
            self.lector_status.config(text="⏸️ LECTOR PAUSADO - Presione para activar", 
                                    foreground=self.COLOR_WARNING)
            self._actualizar_status("Lector pausado")

    def _show_busqueda_avanzada(self):
        """Mostrar diálogo de búsqueda avanzada"""
        dialogo = BusquedaAvanzadaDialog(self)
        self.wait_window(dialogo)
        if hasattr(dialogo, 'producto_seleccionado'):
            self._agregar_producto_desde_datos(dialogo.producto_seleccionado)

    def _show_lista_productos(self):
        """Mostrar diálogo con lista completa de productos"""
        dialogo = ListaProductosDialog(self)
        self.wait_window(dialogo)
        if hasattr(dialogo, 'producto_seleccionado'):
            self._agregar_producto_desde_datos(dialogo.producto_seleccionado)

    def _actualizar_lista_productos(self):
        """Actualizar cache de productos"""
        self._actualizar_status("Actualizando lista de productos...")
        self._actualizar_status("Lista de productos actualizada")

    def _on_doble_clic(self, event):
        """Al hacer doble clic en un item"""
        self._menu_editar_cantidad()

    def _on_clic_derecho(self, event):
        """Al hacer clic derecho en un item"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def _menu_editar_cantidad(self):
        """Editar cantidad del item seleccionado"""
        seleccion = self.tree.selection()
        if not seleccion:
            return
            
        idx = self.tree.index(seleccion[0])
        if 0 <= idx < len(self.items):
            item = self.items[idx]
            nueva_cantidad = tk.simpledialog.askinteger(
                "Editar cantidad",
                f"Nueva cantidad para {item.nombre}:",
                parent=self,
                initialvalue=item.cantidad,
                minvalue=1
            )
            if nueva_cantidad:
                item.cantidad = nueva_cantidad
                self._actualizar_treeview()
                self._actualizar_totales()
                self._actualizar_status(f"Cantidad actualizada: {item.nombre}")

    def _menu_aumentar_1(self):
        """Aumentar cantidad en 1"""
        seleccion = self.tree.selection()
        if not seleccion:
            return
            
        idx = self.tree.index(seleccion[0])
        if 0 <= idx < len(self.items):
            self.items[idx].cantidad += 1
            self._actualizar_treeview()
            self._actualizar_totales()

    def _menu_disminuir_1(self):
        """Disminuir cantidad en 1"""
        seleccion = self.tree.selection()
        if not seleccion:
            return
            
        idx = self.tree.index(seleccion[0])
        if 0 <= idx < len(self.items):
            if self.items[idx].cantidad > 1:
                self.items[idx].cantidad -= 1
                self._actualizar_treeview()
                self._actualizar_totales()

    def _menu_eliminar_item(self):
        """Eliminar item seleccionado"""
        self._eliminar_seleccionado()

    def _menu_ver_info(self):
        """Ver información detallada del producto"""
        seleccion = self.tree.selection()
        if not seleccion:
            return
            
        idx = self.tree.index(seleccion[0])
        if 0 <= idx < len(self.items):
            item = self.items[idx]
            info = f"""
            Información del Producto:
            
            Nombre: {item.nombre}
            Código: {item.codigo_barras}
            Precio: {money(item.precio)}
            Cantidad: {item.cantidad}
            Stock disponible: {item.stock}
            Subtotal: {money(item.subtotal)}
            
            Estado: {'✅ Stock suficiente' if item.tiene_stock else '⚠️ Stock insuficiente'}
            """
            messagebox.showinfo("Información del Producto", info.strip())

    def _eliminar_seleccionado(self):
        """Eliminar item seleccionado"""
        seleccion = self.tree.selection()
        if not seleccion:
            self._actualizar_status("Seleccione un item para eliminar")
            return
            
        idx = self.tree.index(seleccion[0])
        if 0 <= idx < len(self.items):
            item = self.items[idx]
            self.items.pop(idx)
            self._actualizar_treeview()
            self._actualizar_totales()
            self._actualizar_status(f"Eliminado: {item.nombre}")

    def _limpiar_venta(self):
        """Limpiar toda la venta"""
        if not self.items:
            return
            
        if messagebox.askyesno("Limpiar venta", "¿Está seguro de que desea limpiar toda la venta?"):
            self.items.clear()
            self._actualizar_treeview()
            self._actualizar_totales()
            self._actualizar_status("Venta limpiada")
            self.entry_codigo.focus()

    def _finalizar_venta(self):
        """Finalizar y procesar la venta con pago real"""
        if not self.items:
            messagebox.showwarning("Venta vacía", "No hay productos en la venta")
            return

        # Verificar stock
        sin_stock = []
        for item in self.items:
            if item.stock < item.cantidad:
                sin_stock.append({
                    'item': item,
                    'stock_actual': item.stock,
                    'cantidad_solicitada': item.cantidad
                })

        if sin_stock:
            productos_sin_stock = "\n".join([
                f"- {item['item'].nombre}: Stock {item['stock_actual']}, Solicitado {item['cantidad_solicitada']}" 
                for item in sin_stock
            ])
            
            if not messagebox.askyesno("Stock insuficiente", 
                                    f"Los siguientes productos no tienen stock suficiente:\n\n{productos_sin_stock}\n\n¿Desea continuar igualmente?"):
                return

        # Calcular total
        total = sum(float(item.subtotal) for item in self.items)
        
        # Mostrar diálogo de pago
        dialogo_pago = PagoDialog(self, Decimal(total))
        self.wait_window(dialogo_pago)
        
        if not dialogo_pago.resultado:
            return  # Usuario canceló

        # Procesar la venta
        try:
            items_payload = [
                {
                    "producto_id": item.producto_id,
                    "cantidad": item.cantidad,
                    "precio": float(item.precio),
                    "nombre": item.nombre
                }
                for item in self.items
            ]

            # Crear venta en la base de datos
            venta_id = VentaRepo.crear_venta(
                punto_venta_id=self.punto_venta_id,
                items=items_payload,
                forma_pago=dialogo_pago.resultado["forma_pago"],
                monto_recibido=dialogo_pago.resultado["monto_recibido"],
                vuelto=dialogo_pago.resultado["vuelto"]
            )

            # Mostrar resumen de venta
            self._mostrar_resumen_venta(venta_id, dialogo_pago.resultado)
            
            # Limpiar venta
            self._limpiar_venta()
            
        except ValueError as e:
            logger.error(f"Error de stock en venta: {e}")
            messagebox.showerror("Error de Stock", f"No se puede procesar la venta:\n{e}")
        except Exception as e:
            logger.error(f"Error finalizando venta: {e}")
            messagebox.showerror("Error", f"No se pudo procesar la venta: {e}")

    def _mostrar_resumen_venta(self, venta_id: int, datos_pago: Dict):
        """Mostrar resumen completo de la venta procesada"""
        total = sum(float(item.subtotal) for item in self.items)
        
        resumen = f"""
        ✅ VENTA PROCESADA EXITOSAMENTE
        
        📋 DETALLES DE LA VENTA:
        -------------------------
        Ticket: #{venta_id}
        Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Items vendidos: {sum(item.cantidad for item in self.items)}
        
        💰 INFORMACIÓN DE PAGO:
        -----------------------
        Total: {money(total)}
        Forma de pago: {datos_pago['forma_pago']}
        Monto recibido: {money(datos_pago['monto_recibido'])}
        Vuelto: {money(datos_pago['vuelto'])}
        
        📦 PRODUCTOS VENDIDOS:
        ---------------------"""
        
        for item in self.items:
            resumen += f"\n- {item.nombre}: {item.cantidad} x {money(item.precio)} = {money(item.subtotal)}"
        
        resumen += f"\n\n🎉 ¡GRACIAS POR SU COMPRA!"
        
        messagebox.showinfo("Venta Exitosa", resumen)
        
        # Mostrar también el ticket
        self._mostrar_ticket(venta_id, datos_pago)

    def _mostrar_ticket(self, venta_id: int, datos_pago: Dict):
        """Mostrar ticket de venta"""
        try:
            total = sum(float(item.subtotal) for item in self.items)
            
            ticket_window = tk.Toplevel(self)
            ticket_window.title(f"Ticket de Venta #{venta_id}")
            ticket_window.geometry("450x600")
            ticket_window.resizable(False, False)
            
            # Frame principal con scroll
            main_frame = ttk.Frame(ticket_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Texto del ticket
            ticket_text = tk.Text(main_frame, font=("Consolas", 10), wrap="word", 
                                 width=50, height=30)
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=ticket_text.yview)
            ticket_text.configure(yscrollcommand=scrollbar.set)
            
            ticket_text.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            contenido = self._generar_contenido_ticket(venta_id, total, datos_pago)
            ticket_text.insert("1.0", contenido)
            ticket_text.config(state="disabled")
            
            # Botones
            btn_frame = ttk.Frame(ticket_window)
            btn_frame.pack(fill="x", padx=10, pady=10)
            
            ttk.Button(btn_frame, text="🖨️ Imprimir", 
                      command=lambda: self._imprimir_ticket(contenido)).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="💾 Guardar", 
                      command=lambda: self._guardar_ticket(venta_id, contenido)).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="Cerrar", 
                      command=ticket_window.destroy).pack(side="right", padx=5)
                        
        except Exception as e:
            logger.error(f"Error mostrando ticket: {e}")
            messagebox.showerror("Error", f"No se pudo generar el ticket: {e}")

    def _generar_contenido_ticket(self, venta_id: int, total: float, datos_pago: Dict) -> str:
        """Generar contenido del ticket"""
        now = datetime.datetime.now()
        
        # Mapear formas de pago a texto amigable
        formas_pago = {
            "EFECTIVO": "EFECTIVO",
            "TARJETA_DEBITO": "TARJETA DÉBITO",
            "TARJETA_CREDITO": "TARJETA CRÉDITO",
            "TRANSFERENCIA": "TRANSFERENCIA"
        }
        
        contenido = [
            " " * 18 + "KIOSKO PRO",
            " " * 16 + "======================",
            f"Fecha: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Ticket: #{venta_id}",
            " " * 16 + "======================",
            ""
        ]
        
        # Productos
        for item in self.items:
            nombre = item.nombre[:22] + "..." if len(item.nombre) > 22 else item.nombre
            subtotal = item.cantidad * float(item.precio)
            linea = f"{item.cantidad:2d} x {nombre:<25} {money(subtotal):>10}"
            contenido.append(linea)
        
        # Totales y pago
        contenido.extend([
            "",
            " " * 16 + "----------------------",
            f"{'SUBTOTAL:':<35} {money(total):>10}",
            f"{'TOTAL:':<35} {money(total):>10}",
            "",
            f"FORMA DE PAGO: {formas_pago.get(datos_pago['forma_pago'], datos_pago['forma_pago'])}"
        ])
        
        # Información de pago si es efectivo
        if datos_pago['forma_pago'] == "EFECTIVO":
            contenido.extend([
                f"MONTO RECIBIDO: {money(datos_pago['monto_recibido'])}",
                f"VUELTO: {money(datos_pago['vuelto'])}"
            ])
        
        contenido.extend([
            "",
            " " * 14 + "*** GRACIAS POR SU COMPRA ***",
            "",
            " " * 12 + "Venta procesada correctamente"
        ])
        
        return "\n".join(contenido)

    def _imprimir_ticket(self, contenido: str):
        """Imprimir ticket (simulado)"""
        try:
            # En un sistema real, aquí iría el código para imprimir
            # Por ahora simulamos la impresión
            self._actualizar_status("Ticket enviado a impresión")
            messagebox.showinfo("Imprimir", "Ticket enviado a la impresora")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo imprimir: {e}")

    def _guardar_ticket(self, venta_id: int, contenido: str):
        """Guardar ticket en archivo"""
        try:
            os.makedirs("tickets", exist_ok=True)
            filename = f"tickets/venta_{venta_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(contenido)
            self._actualizar_status(f"Ticket guardado: {filename}")
            messagebox.showinfo("Guardado", f"Ticket guardado en:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el ticket: {e}")



class BusquedaAvanzadaDialog(tk.Toplevel):
    """Diálogo de búsqueda avanzada de productos"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.producto_seleccionado = None
        
        self.title("🔍 Búsqueda Avanzada de Productos")
        self.geometry("600x400")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        self._construir_ui()
        self._cargar_productos()
        
    def _construir_ui(self):
        """Construir interfaz del diálogo"""
        search_frame = ttk.Frame(self, padding="10")
        search_frame.pack(fill="x")
        
        ttk.Label(search_frame, text="Buscar:").pack(side="left")
        self.entry_busqueda = ttk.Entry(search_frame, width=40)
        self.entry_busqueda.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_busqueda.bind("<KeyRelease>", self._filtrar_productos)
        
        ttk.Button(search_frame, text="Buscar", 
                  command=self._filtrar_productos).pack(side="left", padx=5)
        
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("codigo", "nombre", "precio", "stock")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col, text, width in [
            ("codigo", "Código", 120),
            ("nombre", "Nombre", 250),
            ("precio", "Precio", 100),
            ("stock", "Stock", 80)
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center")
        
    
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        

        self.tree.bind("<Double-1>", self._seleccionar_producto)
        self.tree.bind("<Return>", self._seleccionar_producto)
        

        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="Seleccionar", 
                  command=self._seleccionar_producto).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancelar", 
                  command=self.destroy).pack(side="right", padx=5)
        
        self.entry_busqueda.focus()
        
    def _cargar_productos(self):
        """Cargar lista de productos"""
        try:
            self.productos = ProductoRepo.listar()
            self._mostrar_productos(self.productos)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los productos: {e}")
            
    def _mostrar_productos(self, productos):
        """Mostrar productos en el treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for prod in productos:
            self.tree.insert("", tk.END, values=(
                prod.get('codigo_barras', ''),
                prod['nombre'],
                f"${float(prod['precio']):.2f}",
                prod.get('stock', 0)
            ))
            
    def _filtrar_productos(self, event=None):
        """Filtrar productos según búsqueda"""
        query = self.entry_busqueda.get().lower().strip()
        if not query:
            self._mostrar_productos(self.productos)
            return
            
        resultados = []
        for prod in self.productos:
            if (query in prod['nombre'].lower() or 
                query in prod.get('codigo_barras', '').lower()):
                resultados.append(prod)
                
        self._mostrar_productos(resultados)
        
    def _seleccionar_producto(self, event=None):
        """Seleccionar producto"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Seleccione un producto")
            return
            
        item = self.tree.item(seleccion[0])
        valores = item['values']
        
        codigo = valores[0]
        for prod in self.productos:
            if prod.get('codigo_barras') == codigo:
                self.producto_seleccionado = prod
                self.destroy()
                return
                
        messagebox.showerror("Error", "No se pudo encontrar el producto seleccionado")

class ListaProductosDialog(BusquedaAvanzadaDialog):
    """Diálogo de lista completa de productos (herencia de búsqueda)"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("📋 Lista Completa de Productos")
        
    def _construir_ui(self):
        """Construir interfaz específica para lista completa"""
        # Frame de información
        info_frame = ttk.Frame(self, padding="10")
        info_frame.pack(fill="x")
        
        ttk.Label(info_frame, 
                 text="Lista completa de productos - Doble clic para seleccionar",
                 font=("Segoe UI", 9)).pack()
        
        # Frame de búsqueda (más simple)
        search_frame = ttk.Frame(self, padding="10")
        search_frame.pack(fill="x")
        
        ttk.Label(search_frame, text="Filtrar:").pack(side="left")
        self.entry_busqueda = ttk.Entry(search_frame, width=40)
        self.entry_busqueda.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_busqueda.bind("<KeyRelease>", self._filtrar_productos)
        
        # Treeview (igual que el padre)
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("codigo", "nombre", "precio", "stock", "categoria")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        
        for col, text, width in [
            ("codigo", "Código", 120),
            ("nombre", "Nombre", 220),
            ("precio", "Precio", 100),
            ("stock", "Stock", 80),
            ("categoria", "Categoría", 120)
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center")
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.bind("<Double-1>", self._seleccionar_producto)
        self.tree.bind("<Return>", self._seleccionar_producto)
        
        # Botones
        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="Seleccionar Producto", 
                  command=self._seleccionar_producto).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cerrar", 
                  command=self.destroy).pack(side="right", padx=5)
        
        self.entry_busqueda.focus()

# Ejecución de prueba
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Sistema de Ventas PRO - Modo Prueba")
    root.geometry("1200x800")
    
    frame = NuevaVentaFrame(root)
    frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    root.mainloop()