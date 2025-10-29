import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from nueva_venta import NuevaVentaFrame
from repos import ProductoRepo, VentaRepo, CategoriaRepo, PuntoVentaRepo
import datetime
from simulacion_ventas import SimulacionVentasFrame
class VentasApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kiosko - Sistema de Venta")
        self.geometry("1300x800")
        self.configure(bg="#f8f9fa")
        
        try:
            self.iconbitmap("kiosko.ico")  
        except:
            pass

        self._setup_modern_styles()
        
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=True)
        
        self._create_header()
        
        self.nb = ttk.Notebook(self.main_frame)
        self.nb.pack(fill="both", expand=True, padx=15, pady=(5, 0))
        
        self._create_tabs()
        
        self._create_status_bar()
        
        self.bind("<F5>", lambda e: self.refresh_all_tabs())
        
    def _setup_modern_styles(self):
        """Configurar estilos modernos y profesionales"""
        style = ttk.Style(self)
        style.theme_use("clam")
        
        colors = {
            "primary": "#2c3e50",
            "secondary": "#3498db", 
            "success": "#27ae60",
            "warning": "#e67e22",
            "danger": "#e74c3c",
            "light": "#ecf0f1",
            "dark": "#34495e"
        }
        
        style.configure("TNotebook", background=colors["light"])
        style.configure("TNotebook.Tab", 
                       padding=(20, 8), 
                       font=("Segoe UI", 10, "bold"),
                       background=colors["light"],
                       foreground=colors["dark"])
        style.map("TNotebook.Tab", 
                 background=[("selected", colors["primary"])],
                 foreground=[("selected", "white")])
        
        style.configure("Treeview", 
                       font=("Segoe UI", 10),
                       rowheight=32,
                       background="white",
                       fieldbackground="white")
        style.configure("Treeview.Heading", 
                       font=("Segoe UI", 10, "bold"),
                       background=colors["primary"],
                       foreground="white",
                       relief="flat")
        style.map("Treeview", 
                 background=[("selected", colors["secondary"])],
                 foreground=[("selected", "white")])
        
        style.configure("Accent.TButton",
                       font=("Segoe UI", 10, "bold"),
                       background=colors["secondary"],
                       foreground="white",
                       padding=(15, 8))
        style.configure("Success.TButton",
                       font=("Segoe UI", 10, "bold"), 
                       background=colors["success"],
                       foreground="white",
                       padding=(15, 8))
        style.configure("Warning.TButton",
                       font=("Segoe UI", 10, "bold"),
                       background=colors["warning"],
                       foreground="white",
                       padding=(15, 8))
        
        style.configure("Header.TFrame", background=colors["primary"])
        style.configure("Card.TFrame", background="white", relief="raised", borderwidth=1)
        
    def _create_header(self):
        """Crear header moderno con información del sistema"""
        header = ttk.Frame(self.main_frame, style="Header.TFrame", height=80)
        header.pack(fill="x", padx=15, pady=(15, 10))
        header.pack_propagate(False)
        
        title_frame = ttk.Frame(header, style="Header.TFrame")
        title_frame.pack(side="left", padx=20)
        
        title = tk.Label(title_frame, 
                        text="🚀 KIOSKO PRO", 
                        font=("Segoe UI", 20, "bold"),
                        background="#2c3e50",
                        foreground="white")
        title.pack(side="left")
        
        subtitle = tk.Label(title_frame,
                           text="Sistema de Ventas Avanzado",
                           font=("Segoe UI", 11),
                           background="#2c3e50", 
                           foreground="#bdc3c7")
        subtitle.pack(side="left", padx=(15, 0))
        
        stats_frame = ttk.Frame(header, style="Header.TFrame")
        stats_frame.pack(side="right", padx=20)
        
        try:
            productos = len(ProductoRepo.listar())
            ventas_hoy = self._get_ventas_hoy()
            
            stats_text = f"📦 {productos} Productos | 🧾 {ventas_hoy} Ventas hoy"
            stats_label = tk.Label(stats_frame,
                                 text=stats_text,
                                 font=("Segoe UI", 10, "bold"),
                                 background="#2c3e50",
                                 foreground="#ecf0f1")
            stats_label.pack(side="right")
            
        except Exception as e:
            print(f"Error cargando stats: {e}")
    
    
    def _create_tabs(self):
        """Crear las pestañas del sistema"""
        self.tab_nueva_venta = NuevaVentaFrame(self.nb)
        self.tab_productos = ProductosFrame(self.nb)
        self.tab_categorias = CategoriasFrame(self.nb) 
        self.tab_historial = HistorialVentasFrame(self.nb)
        self.tab_puntos = PuntosVentaFrame(self.nb)
        self.tab_dashboard = DashboardFrame(self.nb)
        self.tab_simulacion = SimulacionVentasFrame(self.nb)
        
        self.nb.add(self.tab_dashboard, text="📊 Dashboard")
        self.nb.add(self.tab_nueva_venta, text="💰 Nueva Venta")
        self.nb.add(self.tab_productos, text="📦 Productos")
        self.nb.add(self.tab_categorias, text="📂 Categorías")
        self.nb.add(self.tab_historial, text="🧾 Historial Ventas")
        self.nb.add(self.tab_puntos, text="🏪 Puntos de Venta")
        self.nb.add(self.tab_simulacion, text="🎮 Simular Ventas")
        
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_change)
    
    def _create_status_bar(self):
        """Crear barra de estado moderna"""
        status_frame = ttk.Frame(self.main_frame, relief="sunken")
        status_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        self.status_text = tk.StringVar()
        self.status_text.set("Sistema listo - F5 para actualizar toda la información")
        
        status_label = ttk.Label(status_frame, 
                               textvariable=self.status_text,
                               font=("Segoe UI", 9),
                               foreground="#7f8c8d")
        status_label.pack(side="left", padx=10, pady=5)
        
        self.time_label = ttk.Label(status_frame,
                                  font=("Segoe UI", 9),
                                  foreground="#7f8c8d")
        self.time_label.pack(side="right", padx=10, pady=5)
        self._update_time()
    
    def _update_time(self):
        """Actualizar hora en la barra de estado"""
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.time_label.config(text=f"🕒 {now}")
        self.after(1000, self._update_time)
    
    def _get_ventas_hoy(self):
        """Obtener número de ventas de hoy"""
        try:
            ventas = VentaRepo.listar(limit=1000)
            hoy = datetime.datetime.now().date()
            ventas_hoy = sum(1 for v in ventas if v['fecha'].date() == hoy)
            return ventas_hoy
        except:
            return 0
    
    def _on_tab_change(self, event):
        """Cuando se cambia de pestaña"""
        tab_name = self.nb.tab(self.nb.select(), "text")
        self.status_text.set(f"Vista activa: {tab_name}")
        
        if "Dashboard" in tab_name and hasattr(self.tab_dashboard, 'load'):
            self.tab_dashboard.load()
        elif "Productos" in tab_name and hasattr(self.tab_productos, 'load'):
            self.tab_productos.load()
    
    def refresh_all_tabs(self):
        """Actualizar todas las pestañas"""
        self.status_text.set("Actualizando toda la información...")
        
        tabs = [self.tab_dashboard, self.tab_productos, self.tab_categorias, 
                self.tab_historial, self.tab_puntos]
        
        for tab in tabs:
            if hasattr(tab, 'load'):
                try:
                    tab.load()
                except Exception as e:
                    print(f"Error actualizando pestaña: {e}")
        
        self.status_text.set("Sistema actualizado correctamente")
        messagebox.showinfo("Actualizado", "Toda la información ha sido actualizada correctamente")

class ModernBaseFrame(ttk.Frame):
    """Frame base modernizado con herramientas avanzadas"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
    def make_modern_toolbar(self, buttons, title=None):
        """Crear toolbar moderno con título"""
        toolbar_container = ttk.Frame(self, style="Card.TFrame")
        toolbar_container.pack(fill="x", pady=(0, 10))
        
        if title:
            title_frame = ttk.Frame(toolbar_container)
            title_frame.pack(fill="x", padx=15, pady=(10, 5))
            
            title_label = tk.Label(title_frame, 
                                 text=title,
                                 font=("Segoe UI", 14, "bold"),
                                 foreground="#2c3e50")
            title_label.pack(side="left")
        
        toolbar = ttk.Frame(toolbar_container)
        toolbar.pack(fill="x", padx=15, pady=(5, 15))
        
        for text, cmd, style in buttons:
            if style == "accent":
                btn = ttk.Button(toolbar, text=text, command=cmd, style="Accent.TButton")
            elif style == "success":
                btn = ttk.Button(toolbar, text=text, command=cmd, style="Success.TButton")
            elif style == "warning":
                btn = ttk.Button(toolbar, text=text, command=cmd, style="Warning.TButton")
            else:
                btn = ttk.Button(toolbar, text=text, command=cmd)
            
            btn.pack(side="left", padx=3)
        
        ttk.Button(toolbar, text="🔄 Actualizar", 
                  command=getattr(self, 'load', None)).pack(side="right", padx=3)
    
    def create_search_bar(self, placeholder="Buscar...", on_search=None):
        """Crear barra de búsqueda moderna"""
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", pady=(0, 10))
        
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, font=("Segoe UI", 10))
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        search_entry.insert(0, placeholder)
        
        def on_focus_in(event):
            if search_entry.get() == placeholder:
                search_entry.delete(0, tk.END)
                search_entry.config(foreground="black")
        
        def on_focus_out(event):
            if not search_entry.get():
                search_entry.insert(0, placeholder)
                search_entry.config(foreground="gray")
        
        search_entry.bind("<FocusIn>", on_focus_in)
        search_entry.bind("<FocusOut>", on_focus_out)
        search_entry.config(foreground="gray")
        
        ttk.Button(search_frame, text="🔍 Buscar", 
                  command=lambda: on_search(search_var.get())).pack(side="left", padx=(0, 5))
        
        ttk.Button(search_frame, text="🗑️ Limpiar", 
                  command=lambda: [search_var.set(""), on_search("")]).pack(side="left")
        
        return search_var
    
    def create_modern_treeview(self, columns_config, height=15):
        """Crear treeview moderno con scrollbars"""
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        
        columns = [col[0] for col in columns_config]
        tree = ttk.Treeview(container, columns=columns, show="headings", height=height)
        
        for col_id, heading, width, anchor in columns_config:
            tree.heading(col_id, text=heading)
            tree.column(col_id, width=width, anchor=anchor)
        
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        h_scroll = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        
        tree.tag_configure("even", background="#f8f9fa")
        tree.tag_configure("odd", background="white")
        tree.tag_configure("warning", background="#fff3cd")
        tree.tag_configure("danger", background="#f8d7da")
        tree.tag_configure("inactive", background="#e9ecef", foreground="#6c757d")  # Gris para inactivos
        
        return tree

class DashboardFrame(ModernBaseFrame):
    """Dashboard moderno con métricas y gráficos"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.load()
    
    def load(self):
        """Cargar datos del dashboard"""
        for widget in self.winfo_children():
            widget.destroy()
        
        self.make_modern_toolbar([
            ("📊 Actualizar Métricas", self.load, "accent"),
            ("📈 Reporte Completo", self.generar_reporte, "success")
        ], "📊 Dashboard de Ventas")
        
        self._create_metrics_cards()
        
        self._create_recent_sales()
    
    def _create_metrics_cards(self):
        """Crear tarjetas de métricas"""
        metrics_frame = ttk.Frame(self)
        metrics_frame.pack(fill="x", pady=(0, 20))
        
        try:
            productos = ProductoRepo.listar()
            ventas = VentaRepo.listar(limit=100)
            ventas_hoy = self._get_ventas_hoy()
            total_ventas = sum(v['total'] for v in ventas)
            productos_bajo_stock = sum(1 for p in productos if p['stock'] < 10)
            
            metrics = [
                ("📦 Total Productos", len(productos), "#3498db", "productos"),
                ("🧾 Ventas Hoy", ventas_hoy, "#27ae60", "ventas"), 
                ("💰 Ingresos Totales", f"${total_ventas:,.2f}", "#9b59b6", "ingresos"),
                ("⚠️ Stock Bajo", productos_bajo_stock, "#e74c3c", "stock")
            ]
            
            for i, (title, value, color, key) in enumerate(metrics):
                card = self._create_metric_card(metrics_frame, title, value, color)
                card.pack(side="left", fill="x", expand=True, padx=5)  # CORREGIDO: usar pack en lugar de grid
                
        except Exception as e:
            print(f"Error cargando métricas: {e}")
    
    def _create_metric_card(self, parent, title, value, color):
        """Crear tarjeta de métrica individual"""
        card = tk.Frame(parent, bg="white", relief="raised", borderwidth=1, width=200, height=100)
        
        title_label = tk.Label(card, text=title, bg="white", 
                              font=("Segoe UI", 10, "bold"),
                              foreground="#7f8c8d")
        title_label.pack(pady=(15, 5))
        
        value_label = tk.Label(card, text=value, bg="white",
                              font=("Segoe UI", 18, "bold"), 
                              foreground=color)
        value_label.pack(pady=(0, 15))
        
        color_bar = tk.Frame(card, bg=color, height=4)
        color_bar.pack(fill="x", side="bottom")
        
        return card
    
    def _create_recent_sales(self):
        """Crear tabla de ventas recientes"""
        recent_frame = ttk.LabelFrame(self, text="🕒 Ventas Recientes", padding=10)
        recent_frame.pack(fill="both", expand=True)
        
        columns = [
            ("id", "ID", 60, "center"),
            ("fecha", "Fecha", 150, "center"),
            ("total", "Total", 100, "center"), 
            ("pago", "Forma Pago", 120, "center")
        ]
        
        self.sales_tree = ttk.Treeview(recent_frame, columns=[col[0] for col in columns], show="headings", height=8)
        
        for col_id, heading, width, anchor in columns:
            self.sales_tree.heading(col_id, text=heading)
            self.sales_tree.column(col_id, width=width, anchor=anchor)
        
        v_scroll = ttk.Scrollbar(recent_frame, orient="vertical", command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=v_scroll.set)
        
        self.sales_tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        
        self.sales_tree.tag_configure("even", background="#f8f9fa")
        self.sales_tree.tag_configure("odd", background="white")
        
        try:
            ventas = VentaRepo.listar(limit=20)
            for idx, venta in enumerate(ventas):
                tag = "even" if idx % 2 == 0 else "odd"
                self.sales_tree.insert("", tk.END, values=(
                    venta["id"],
                    venta["fecha"].strftime("%d/%m/%Y %H:%M"),
                    f"${venta['total']:.2f}",
                    venta["forma_pago"]
                ), tags=(tag,))
        except Exception as e:
            print(f"Error cargando ventas recientes: {e}")
    
    def _get_ventas_hoy(self):
        """Obtener ventas de hoy"""
        try:
            ventas = VentaRepo.listar(limit=1000)
            hoy = datetime.datetime.now().date()
            return sum(1 for v in ventas if v['fecha'].date() == hoy)
        except:
            return 0
    
    def generar_reporte(self):
        """Generar reporte completo"""
        messagebox.showinfo("Reporte", "Función de reportes en desarrollo...")
class ProductosFrame(ModernBaseFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.toolbar_buttons = [
            ("➕ Agregar Producto", self.add, "success"),
            ("✏️ Editar Seleccionado", self.edit, "accent"),
            ("📊 Actualizar Precio", self.actualizar_precio, "warning"),
            ("🔄 Activar/Desactivar", self.toggle_estado, "danger")
        ]
        
        self.make_modern_toolbar(self.toolbar_buttons, "📦 Gestión de Productos")
        
        self._create_status_filter()
        
        self.search_var = self.create_search_bar("Buscar productos...", self.buscar_productos)
        
        columns = [
            ("id", "ID", 70, "center"),
            ("codigo", "Código", 130, "center"),
            ("nombre", "Nombre", 250, "w"),
            ("precio", "Precio", 100, "center"),
            ("stock", "Stock", 80, "center"),
            ("categoria", "Categoría", 120, "center"),
            ("estado", "Estado", 100, "center")
        ]
        
        self.tree = self.create_modern_treeview(columns)
        
        self.tree.bind("<Double-1>", lambda e: self.edit())
        self.tree.bind("<Delete>", lambda e: self.toggle_estado())
        
        self.load()

    def _create_status_filter(self):
        """Crear filtro por estado"""
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filtrar por estado:", font=("Segoe UI", 9)).pack(side="left", padx=(0, 10))
        
        self.filter_var = tk.StringVar(value="TODOS")
        
        ttk.Radiobutton(filter_frame, text="Todos", variable=self.filter_var, 
                       value="TODOS", command=self.load).pack(side="left", padx=(0, 10))
        ttk.Radiobutton(filter_frame, text="Activos", variable=self.filter_var, 
                       value="ACTIVOS", command=self.load).pack(side="left", padx=(0, 10))
        ttk.Radiobutton(filter_frame, text="Inactivos", variable=self.filter_var, 
                       value="INACTIVOS", command=self.load).pack(side="left")

    def load(self):
        """Cargar productos con filtro de estado"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            productos = ProductoRepo.listar()
            for idx, p in enumerate(productos):
                estado = "ACTIVO" if p.get('activo', True) else "INACTIVO"
                filtro = self.filter_var.get()
                
                if filtro == "ACTIVOS" and estado != "ACTIVO":
                    continue
                if filtro == "INACTIVOS" and estado != "INACTIVO":
                    continue
                
                tags = ("even",) if idx % 2 == 0 else ("odd",)
                
                if p['stock'] < 5:
                    tags += ("warning",)
                if p['stock'] == 0:
                    tags += ("danger",)
                if estado == "INACTIVO":
                    tags += ("inactive",)
                
                self.tree.insert("", tk.END, values=(
                    p["id"],
                    p["codigo_barras"],
                    p["nombre"],
                    f"${p['precio']:.2f}",
                    p["stock"],
                    p["categoria"],
                    estado
                ), tags=tags)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los productos:\n{str(e)}")

    def buscar_productos(self, query):
        """Buscar productos con filtro de estado"""
        if not query or query == "Buscar productos...":
            self.load()
            return
            
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            productos = ProductoRepo.listar()
            for idx, p in enumerate(productos):
                if not (query.lower() in p['nombre'].lower() or 
                       query.lower() in p.get('codigo_barras', '').lower() or
                       query.lower() in p.get('categoria', '').lower()):
                    continue
                
                # Aplicar filtro de estado
                estado = "ACTIVO" if p.get('activo', True) else "INACTIVO"
                filtro = self.filter_var.get()
                
                if filtro == "ACTIVOS" and estado != "ACTIVO":
                    continue
                if filtro == "INACTIVOS" and estado != "INACTIVO":
                    continue
                    
                tags = ("even",) if idx % 2 == 0 else ("odd",)
                if p['stock'] < 5:
                    tags += ("warning",)
                # Resaltar productos inactivos
                if estado == "INACTIVO":
                    tags += ("inactive",)
                
                self.tree.insert("", tk.END, values=(
                    p["id"],
                    p["codigo_barras"], 
                    p["nombre"],
                    f"${p['precio']:.2f}",
                    p["stock"],
                    p["categoria"],
                    estado
                ), tags=tags)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error en búsqueda: {str(e)}")

    def toggle_estado(self):
        """Activar/Desactivar producto seleccionado"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Seleccione un producto para cambiar su estado")
            return
            
        producto_id = self.tree.item(seleccion[0])["values"][0]
        producto_nombre = self.tree.item(seleccion[0])["values"][2]
        estado_actual = self.tree.item(seleccion[0])["values"][6]
        
        nuevo_estado = not (estado_actual == "ACTIVO")
        accion = "activar" if nuevo_estado else "desactivar"
        
        if messagebox.askyesno("Confirmar", 
                             f"¿Está seguro de {accion} el producto '{producto_nombre}'?"):
            try:
                producto = ProductoRepo.buscar_por_id(producto_id)
                if producto:
                    ProductoRepo.actualizar_completo(
                        producto_id=producto_id,
                        nombre=producto['nombre'],
                        precio=producto['precio'],
                        codigo_barras=producto.get('codigo_barras'),
                        categoria_id=producto.get('categoria_id'),
                        stock=producto.get('stock'),
                        activo=nuevo_estado
                    )
                    self.load()
                    estado_text = "activado" if nuevo_estado else "desactivado"
                    messagebox.showinfo("Éxito", f"Producto {estado_text} correctamente")
                else:
                    messagebox.showerror("Error", "No se pudo encontrar el producto")
                    
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cambiar el estado del producto:\n{str(e)}")

    def add(self):
        """Agregar nuevo producto"""
        dialog = ProductoDialog(self, "Nuevo Producto")
        self.wait_window(dialog)
        if dialog.resultado:
            self.load()

    def edit(self):
        """Editar producto seleccionado"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Seleccione un producto para editar")
            return
            
        producto_id = self.tree.item(seleccion[0])["values"][0]
        dialog = ProductoDialog(self, "Editar Producto", producto_id)
        self.wait_window(dialog)
        if dialog.resultado:
            self.load()

    def actualizar_precio(self):
        """Actualizar precio rápido"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Seleccione un producto")
            return
            
        producto_id = self.tree.item(seleccion[0])["values"][0]
        producto_nombre = self.tree.item(seleccion[0])["values"][2]
        estado_actual = self.tree.item(seleccion[0])["values"][6]
        
        if estado_actual == "INACTIVO":
            messagebox.showwarning("Producto Inactivo", "No se puede actualizar el precio de un producto inactivo")
            return
        
        nuevo_precio = simpledialog.askfloat(
            "Actualizar Precio",
            f"Nuevo precio para {producto_nombre}:",
            initialvalue=float(self.tree.item(seleccion[0])["values"][3].replace('$', '')),
            minvalue=0.0
        )
        
        if nuevo_precio:
            try:
                ProductoRepo.actualizar_precio(producto_id, nuevo_precio)
                self.load()
                messagebox.showinfo("Éxito", "Precio actualizado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar el precio:\n{str(e)}")
                
class ProductoDialog(tk.Toplevel):
    """Diálogo moderno para agregar/editar productos - CORREGIDO"""
    
    def __init__(self, parent, titulo, producto_id=None):
        super().__init__(parent)
        self.parent = parent
        self.producto_id = producto_id
        self.resultado = False
        
        self.title(titulo)
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self._construir_ui()
        self._cargar_datos()
        
    def _construir_ui(self):
        """Construir interfaz del diálogo"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text=self.title(), 
                 font=("Segoe UI", 14, "bold")).pack(pady=(0, 20))
        
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill="x", pady=10)
        
        ttk.Label(form_frame, text="Nombre del Producto:*").grid(row=0, column=0, sticky="w", pady=8)
        self.nombre_var = tk.StringVar()
        self.nombre_entry = ttk.Entry(form_frame, textvariable=self.nombre_var, width=40, font=("Segoe UI", 10))
        self.nombre_entry.grid(row=0, column=1, sticky="ew", pady=8, padx=(10, 0))
        
        ttk.Label(form_frame, text="Código de Barras:").grid(row=1, column=0, sticky="w", pady=8)
        self.codigo_var = tk.StringVar()
        self.codigo_entry = ttk.Entry(form_frame, textvariable=self.codigo_var, width=40, font=("Segoe UI", 10))
        self.codigo_entry.grid(row=1, column=1, sticky="ew", pady=8, padx=(10, 0))
        
        ttk.Label(form_frame, text="Precio:*").grid(row=2, column=0, sticky="w", pady=8)
        self.precio_var = tk.StringVar()
        self.precio_entry = ttk.Entry(form_frame, textvariable=self.precio_var, width=20, font=("Segoe UI", 10))
        self.precio_entry.grid(row=2, column=1, sticky="w", pady=8, padx=(10, 0))
        
        ttk.Label(form_frame, text="Stock:*").grid(row=3, column=0, sticky="w", pady=8)
        self.stock_var = tk.StringVar()
        self.stock_entry = ttk.Entry(form_frame, textvariable=self.stock_var, width=20, font=("Segoe UI", 10))
        self.stock_entry.grid(row=3, column=1, sticky="w", pady=8, padx=(10, 0))
        
        ttk.Label(form_frame, text="Categoría:").grid(row=4, column=0, sticky="w", pady=8)
        
        cat_frame = ttk.Frame(form_frame)
        cat_frame.grid(row=4, column=1, sticky="ew", pady=8, padx=(10, 0))
        
        self.categoria_id_var = tk.StringVar()
        self.categoria_combo = ttk.Combobox(cat_frame, textvariable=self.categoria_id_var, state="readonly", width=37)
        self.categoria_combo.pack(side="left", fill="x", expand=True)
        
        self._cargar_categorias()
        
        form_frame.grid_columnconfigure(1, weight=1)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(20, 0))
        
        ttk.Button(btn_frame, text="💾 Guardar", style="Success.TButton",
                  command=self._guardar).pack(side="left", padx=(0, 10))
        ttk.Button(btn_frame, text="❌ Cancelar",
                  command=self.destroy).pack(side="left")
        
        self.nombre_entry.focus()
        
    def _cargar_categorias(self):
        """Cargar categorías en el combobox"""
        try:
            categorias = CategoriaRepo.listar()
            self.categorias_map = {}
            nombres_categorias = []
            
            for cat in categorias:
                self.categorias_map[cat['nombre']] = cat['id']
                nombres_categorias.append(cat['nombre'])
            
            self.categoria_combo['values'] = nombres_categorias
            if nombres_categorias:
                self.categoria_combo.current(0)
                
        except Exception as e:
            print(f"Error cargando categorías: {e}")
            self.categoria_combo['values'] = []
    
    def _cargar_datos(self):
        """Cargar datos si es edición"""
        if self.producto_id:
            try:
                producto = ProductoRepo.buscar_por_id(self.producto_id)
                if producto:
                    self.nombre_var.set(producto['nombre'])
                    self.codigo_var.set(producto.get('codigo_barras', ''))
                    self.precio_var.set(str(producto['precio']))
                    self.stock_var.set(str(producto['stock']))
                    
                    if producto.get('categoria'):
                        for nombre, cat_id in self.categorias_map.items():
                            if cat_id == producto.get('categoria_id'):
                                self.categoria_id_var.set(nombre)
                                break
                    elif producto.get('categoria_id'):
                        for nombre, cat_id in self.categorias_map.items():
                            if cat_id == producto.get('categoria_id'):
                                self.categoria_id_var.set(nombre)
                                break
                    
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron cargar los datos:\n{str(e)}")
    
    def _validar_formulario(self):
        """Validar formulario"""
        if not self.nombre_var.get().strip():
            messagebox.showwarning("Validación", "El nombre del producto es obligatorio")
            return False
        
        try:
            precio = float(self.precio_var.get())
            if precio < 0:
                messagebox.showwarning("Validación", "El precio no puede ser negativo")
                return False
        except ValueError:
            messagebox.showwarning("Validación", "El precio debe ser un número válido")
            return False
        
        try:
            stock = int(self.stock_var.get())
            if stock < 0:
                messagebox.showwarning("Validación", "El stock no puede ser negativo")
                return False
        except ValueError:
            messagebox.showwarning("Validación", "El stock debe ser un número entero válido")
            return False
        
        return True
    
    def _guardar(self):
        """Guardar producto - CORREGIDO para usar los métodos correctos"""
        if not self._validar_formulario():
            return
            
        try:
            nombre = self.nombre_var.get().strip()
            codigo = self.codigo_var.get().strip()
            precio = float(self.precio_var.get())
            stock = int(self.stock_var.get())
            
            categoria_id = None
            categoria_nombre = self.categoria_id_var.get()
            if categoria_nombre and hasattr(self, 'categorias_map'):
                categoria_id = self.categorias_map.get(categoria_nombre)
            
            if self.producto_id:
                ProductoRepo.actualizar_completo(
                    producto_id=self.producto_id,
                    nombre=nombre,
                    precio=precio,
                    codigo_barras=codigo if codigo else None,
                    categoria_id=categoria_id,
                    stock=stock
                )
                messagebox.showinfo("Éxito", "✅ Producto actualizado correctamente")
            else:
                ProductoRepo.agregar(
                    nombre=nombre,
                    precio=precio,
                    stock=stock,
                    categoria_id=categoria_id,
                    codigo=codigo if codigo else None
                )
                messagebox.showinfo("Éxito", "✅ Producto agregado correctamente")
            
            self.resultado = True
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"❌ No se pudo guardar el producto:\n{str(e)}")

class CategoriaDialog(tk.Toplevel):
    """Diálogo moderno para agregar/editar categorías - CORREGIDO"""
    
    def __init__(self, parent, titulo, categoria_id=None):
        super().__init__(parent)
        self.parent = parent
        self.categoria_id = categoria_id
        self.resultado = False
        
        self.title(titulo)
        self.geometry("500x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self._construir_ui()
        self._cargar_datos()
        
    def _construir_ui(self):
        """Construir interfaz del diálogo"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text=self.title(), 
                 font=("Segoe UI", 14, "bold")).pack(pady=(0, 20))
        
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill="x", pady=10)
        
        ttk.Label(form_frame, text="Nombre de la Categoría:*", 
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=12)
        self.nombre_var = tk.StringVar()
        self.nombre_entry = ttk.Entry(form_frame, textvariable=self.nombre_var, 
                                     width=40, font=("Segoe UI", 10))
        self.nombre_entry.grid(row=0, column=1, sticky="ew", pady=12, padx=(15, 0))
        
        ttk.Label(form_frame, text="Descripción:", 
                 font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="nw", pady=12)
        self.descripcion_text = tk.Text(form_frame, width=40, height=6, 
                                       font=("Segoe UI", 10), wrap="word")
        self.descripcion_text.grid(row=1, column=1, sticky="ew", pady=12, padx=(15, 0))
        
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=self.descripcion_text.yview)
        self.descripcion_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=2, sticky="ns", pady=12)
        
        self.info_frame = ttk.Frame(form_frame)
        self.info_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(15, 5))
        
        form_frame.grid_columnconfigure(1, weight=1)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(20, 0))
        
        ttk.Button(btn_frame, text="💾 Guardar", style="Success.TButton",
                  command=self._guardar).pack(side="left", padx=(0, 10))
        ttk.Button(btn_frame, text="❌ Cancelar",
                  command=self.destroy).pack(side="left")
        
        self.nombre_entry.focus()
        
    def _cargar_datos(self):
        """Cargar datos si es edición"""
        if self.categoria_id:
            try:
                categoria = CategoriaRepo.buscar_por_id(self.categoria_id)
                
                if categoria:
                    self.nombre_var.set(categoria['nombre'])
                    if categoria.get('descripcion'):
                        self.descripcion_text.insert("1.0", categoria['descripcion'])
                    
                    productos = ProductoRepo.listar()
                    productos_categoria = [p for p in productos if p.get('categoria_id') == self.categoria_id]
                    
                    if productos_categoria:
                        info_text = f"📦 Esta categoría tiene {len(productos_categoria)} productos asociados"
                        info_label = ttk.Label(self.info_frame, text=info_text, 
                                             font=("Segoe UI", 9, "italic"),
                                             foreground="#6c757d")
                        info_label.pack(anchor="w")
                        
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron cargar los datos:\n{str(e)}")
    
    def _validar_formulario(self):
        """Validar formulario"""
        nombre = self.nombre_var.get().strip()
        
        if not nombre:
            messagebox.showwarning("Validación", "El nombre de la categoría es obligatorio")
            return False
        
        if len(nombre) < 2:
            messagebox.showwarning("Validación", "El nombre debe tener al menos 2 caracteres")
            return False
        
        try:
            categorias = CategoriaRepo.listar()
            for cat in categorias:
                if cat['nombre'].lower() == nombre.lower():
                    if self.categoria_id and cat['id'] == self.categoria_id:
                        continue
                    messagebox.showwarning("Validación", f"Ya existe una categoría con el nombre '{nombre}'")
                    return False
        except:
            pass  
        
        return True
    
    def _guardar(self):
        """Guardar categoría - CORREGIDO"""
        if not self._validar_formulario():
            return
            
        try:
            nombre = self.nombre_var.get().strip()
            descripcion = self.descripcion_text.get("1.0", "end-1c").strip()
            
            if self.categoria_id:
                CategoriaRepo.actualizar(self.categoria_id, nombre, descripcion if descripcion else None)
                messagebox.showinfo("Éxito", "✅ Categoría actualizada correctamente")
            else:
                CategoriaRepo.agregar(nombre, descripcion if descripcion else None)
                messagebox.showinfo("Éxito", "✅ Categoría agregada correctamente")
            
            self.resultado = True
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"❌ No se pudo guardar la categoría:\n{str(e)}")


class CategoriasFrame(ModernBaseFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.make_modern_toolbar([
            ("➕ Agregar Categoría", self.agregar_categoria, "success"),
            ("✏️ Editar Seleccionada", self.editar_categoria, "accent"),
            ("🗑️ Eliminar Seleccionada", self.eliminar_categoria, "danger")
        ], "📂 Gestión de Categorías")
        
        self.search_var = self.create_search_bar("Buscar categorías...", self.buscar_categorias)
        
        columns = [
            ("id", "ID", 80, "center"),
            ("nombre", "Nombre", 250, "w"),
            ("descripcion", "Descripción", 400, "w"),
        ]
        
        self.tree = self.create_modern_treeview(columns)
        
        self.tree.bind("<Double-1>", lambda e: self.editar_categoria())
        self.tree.bind("<Delete>", lambda e: self.eliminar_categoria())
        
        self.load()

    def load(self):
        """Cargar categorías con conteo de productos"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            categorias = CategoriaRepo.listar()
            productos = ProductoRepo.listar()
            
            productos_por_categoria = {}
            for producto in productos:
                cat_id = producto.get('categoria_id')
                if cat_id:
                    productos_por_categoria[cat_id] = productos_por_categoria.get(cat_id, 0) + 1
            
            for idx, categoria in enumerate(categorias):
                tag = "even" if idx % 2 == 0 else "odd"
                num_productos = productos_por_categoria.get(categoria['id'], 0)
                
                self.tree.insert("", tk.END, values=(
                    categoria["id"],
                    categoria["nombre"],
                    categoria["descripcion"] or "Sin descripción",
                    f"{num_productos} productos"
                ), tags=(tag,))
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las categorías:\n{str(e)}")

    def buscar_categorias(self, query):
        """Buscar categorías por nombre o descripción"""
        if not query or query == "Buscar categorías...":
            self.load()
            return
            
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            categorias = CategoriaRepo.listar()
            productos = ProductoRepo.listar()
            
            productos_por_categoria = {}
            for producto in productos:
                cat_id = producto.get('categoria_id')
                if cat_id:
                    productos_por_categoria[cat_id] = productos_por_categoria.get(cat_id, 0) + 1
            
            for idx, categoria in enumerate(categorias):
                if not (query.lower() in categoria['nombre'].lower() or 
                       query.lower() in (categoria.get('descripcion') or '').lower()):
                    continue
                    
                tag = "even" if idx % 2 == 0 else "odd"
                num_productos = productos_por_categoria.get(categoria['id'], 0)
                
                self.tree.insert("", tk.END, values=(
                    categoria["id"],
                    categoria["nombre"],
                    categoria["descripcion"] or "Sin descripción",
                    f"{num_productos} productos"
                ), tags=(tag,))
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error en búsqueda: {str(e)}")

    def agregar_categoria(self):
        """Agregar nueva categoría"""
        dialog = CategoriaDialog(self, "Nueva Categoría")
        self.wait_window(dialog)
        if dialog.resultado:
            self.load()

    def editar_categoria(self):
        """Editar categoría seleccionada"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Seleccione una categoría para editar")
            return
            
        categoria_id = self.tree.item(seleccion[0])["values"][0]
        dialog = CategoriaDialog(self, "Editar Categoría", categoria_id)
        self.wait_window(dialog)
        if dialog.resultado:
            self.load()

    def eliminar_categoria(self):
        """Eliminar categoría seleccionada (si no tiene productos) - CORREGIDO"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Seleccione una categoría para eliminar")
            return
            
        categoria_id = self.tree.item(seleccion[0])["values"][0]
        categoria_nombre = self.tree.item(seleccion[0])["values"][1]
        num_productos = int(self.tree.item(seleccion[0])["values"][3].split()[0])
        
        if num_productos > 0:
            messagebox.showerror(
                "Error", 
                f"No se puede eliminar la categoría '{categoria_nombre}'\n\n"
                f"Tiene {num_productos} productos asociados.\n"
                f"Reasigne los productos a otra categoría antes de eliminar."
            )
            return
        
        if messagebox.askyesno(
            "Confirmar Eliminación", 
            f"¿Está seguro de que desea eliminar la categoría '{categoria_nombre}'?\n\n"
            "Esta acción no se puede deshacer."
        ):
            try:
                CategoriaRepo.eliminar(categoria_id)
                messagebox.showinfo("Éxito", "✅ Categoría eliminada correctamente")
                self.load()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar la categoría:\n{str(e)}")

class HistorialVentasFrame(ModernBaseFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.make_modern_toolbar([
            ("📊 Generar Reporte", self.generar_reporte, "accent"),
            ("📋 Ver Detalles", self.ver_detalles, "success")
        ], "🧾 Historial de Ventas")
        
        columns = [
            ("id", "ID", 80, "center"),
            ("fecha", "Fecha y Hora", 180, "center"),
            ("total", "Total", 120, "center"),
            ("forma_pago", "Forma de Pago", 150, "center")
        ]
        
        self.tree = self.create_modern_treeview(columns)
        self.load()
    
    def load(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for idx, v in enumerate(VentaRepo.listar(limit=100)):
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", tk.END, values=(
                v["id"],
                v["fecha"].strftime("%d/%m/%Y %H:%M"),
                f"${v['total']:.2f}",
                v["forma_pago"]
            ), tags=(tag,))
    
    def generar_reporte(self):
        messagebox.showinfo("Reportes", "Sistema de reportes en desarrollo")
    
    def ver_detalles(self):
        seleccion = self.tree.selection()
        if seleccion:
            venta_id = self.tree.item(seleccion[0])["values"][0]
            messagebox.showinfo("Detalles", f"Detalles de venta #{venta_id} en desarrollo")

class PuntosVentaFrame(ModernBaseFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.make_modern_toolbar([
            ("➕ Agregar Punto", self.add, "success"),
            ("✏️ Editar Seleccionado", self.edit, "accent")
        ], "🏪 Puntos de Venta")
        
        columns = [
            ("id", "ID", 80, "center"),
            ("nombre", "Nombre", 200, "w"),
            ("direccion", "Dirección", 300, "w"),
            ("telefono", "Teléfono", 150, "center")
        ]
        
        self.tree = self.create_modern_treeview(columns)
        self.load()
    
    def load(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for idx, p in enumerate(PuntoVentaRepo.listar()):
            tag = "even" if idx % 2 == 0 else ("odd",)
            self.tree.insert("", tk.END, values=(
                p["id"], p["nombre"], p["direccion"], p["telefono"]
            ), tags=(tag,))
    
    def add(self):
        nombre = simpledialog.askstring("Nuevo Punto", "Nombre del punto de venta:")
        if nombre:
            direccion = simpledialog.askstring("Nuevo Punto", "Dirección:")
            telefono = simpledialog.askstring("Nuevo Punto", "Teléfono:")
            PuntoVentaRepo.agregar(nombre, direccion, telefono)
            self.load()
    
    def edit(self):
        seleccion = self.tree.selection() 
        if seleccion:
            messagebox.showinfo("En desarrollo", "Edición de puntos de venta en desarrollo")

if __name__ == "__main__":
    app = VentasApp()
    app.mainloop()