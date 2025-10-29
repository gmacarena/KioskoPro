import tkinter as tk
from tkinter import ttk, messagebox
import sys, traceback

# ─────────────────────────────────────────────────────────────────────
# Importar tu app real del POS
# ─────────────────────────────────────────────────────────────────────
try:
    from ventas_app import VentasApp
except Exception as e:
    print("Error importando ventas_app.VentasApp. Asegúrate de que 'ventas_app.py' está junto a este archivo.")
    traceback.print_exc()
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────
# Usuarios y Roles
# ─────────────────────────────────────────────────────────────────────
USUARIOS = {
    "admin":    {"password": "admin",    "rol": "admin"},
    "cajero1":  {"password": "cajero",   "rol": "cajero"},
    "cajero2":  {"password": "cajero",   "rol": "cajero"},
    "deposito": {"password": "deposito", "rol": "deposito"},
}

# Pestañas permitidas por rol (coinciden con los títulos del Notebook en ventas_app)
TABS_POR_ROL = {
    "admin": {
        "📊 Dashboard",
        "💰 Nueva Venta",
        "📦 Productos",
        "📂 Categorías",
        "🧾 Historial Ventas",
        "🏪 Puntos de Venta",
        "🎮 Simular Ventas",
    },
    "cajero": {
        "💰 Nueva Venta",
        "📦 Productos",
        "📂 Categorías",
    },
    "deposito": {
        "📦 Productos",
    },
}
TAB_INICIAL_POR_ROL = {
    "admin": "📊 Dashboard",
    "cajero": "💰 Nueva Venta",
    "deposito": "📦 Productos",
}

# ─────────────────────────────────────────────────────────────────────
# Subclase del POS con permisos + Cerrar sesión (menú, botón y atajos)
# ─────────────────────────────────────────────────────────────────────
class VentasAppConPermisos(VentasApp):
    def __init__(self, usuario: str, rol: str, *args, **kwargs):
        self.usuario = usuario
        self.rol = rol
        super().__init__(*args, **kwargs)

        try:
            self.title(f"Kiosko - Sistema de Venta | Usuario: {usuario} | Rol: {rol}")
        except Exception:
            pass

        # 1) Menú "Cuenta → Cerrar sesión"
        self._insertar_menu_logout()

        # 2) Barra superior con botón "Cerrar sesión" (visible siempre)
        self._insertar_toolbar_logout()

        # 3) Atajos de teclado
        self.bind_all("<Control-l>", lambda e: self._logout())
        self.bind_all("<Control-L>", lambda e: self._logout())

        # Aplicar permisos de pestañas
        self._aplicar_permisos()

        # Ir a la pestaña inicial sugerida por rol
        self.ir_a(TAB_INICIAL_POR_ROL.get(rol, "📊 Dashboard"))

    def _aplicar_permisos(self):
        permitidas = TABS_POR_ROL.get(self.rol, set())
        try:
            for tab_id in list(self.nb.tabs()):
                titulo = self.nb.tab(tab_id, "text")
                if titulo not in permitidas:
                    self.nb.hide(tab_id)
        except Exception as e:
            messagebox.showerror("Permisos", f"No se pudieron aplicar permisos.\n\n{e}")

    def ir_a(self, titulo_tab: str):
        try:
            for tab_id in self.nb.tabs():
                if self.nb.tab(tab_id, "text") == titulo_tab:
                    self.nb.select(tab_id)
                    return
        except Exception:
            pass

    def _insertar_menu_logout(self):
        # Reusar menubar existente o crear uno
        try:
            menubar = self.nametowidget(self["menu"]) if self["menu"] else None
        except Exception:
            menubar = None

        if menubar is None:
            menubar = tk.Menu(self)
            self.config(menu=menubar)

        cuenta_menu = tk.Menu(menubar, tearoff=0)
        cuenta_menu.add_command(label="Cerrar sesión\tCtrl+L", command=self._logout)
        menubar.add_cascade(label="Cuenta", menu=cuenta_menu)

    def _insertar_toolbar_logout(self):
        """
        Crea una barrita superior propia con un botón 'Cerrar sesión'.
        La insertamos ANTES del main_frame si existe; si no, la ponemos arriba.
        """
        try:
            # Si VentasApp creó self.main_frame, insertamos una barra antes de él
            barra = ttk.Frame(self, padding=(8, 4))
            barra.pack(side="top", fill="x")  # ya queda arriba

            ttk.Label(barra, text=f"Usuario: {self.usuario}  |  Rol: {self.rol}",
                      font=("Segoe UI", 9, "bold")).pack(side="left")

            btn = ttk.Button(barra, text="Cerrar sesión", command=self._logout)
            btn.pack(side="right")
        except Exception as e:
            print("No se pudo crear la barra superior de logout:", e)

    def _logout(self):
        if not messagebox.askyesno("Cerrar sesión", "¿Seguro que deseas cerrar sesión?"):
            return
        try:
            self.destroy()
        finally:
            abrir_login()

# ─────────────────────────────────────────────────────────────────────
# Login Moderno (card) con botón visible (tk.Button)
# ─────────────────────────────────────────────────────────────────────
class LoginApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Iniciar sesión | Kiosko Pro")
        self.geometry("520x380")
        self.minsize(500, 360)
        self.configure(bg="#e9eef3")
        self._setup_style()
        self._build_ui()

    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Paleta
        self.colors = {
            "bg": "#e9eef3",
            "card": "#ffffff",
            "primary": "#2c3e50",
            "secondary": "#3498db",
            "muted": "#7f8c8d",
            "danger": "#e74c3c",
            "success": "#27ae60"
        }

        style.configure("Card.TFrame", background=self.colors["card"])
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"),
                        foreground=self.colors["primary"], background=self.colors["card"])
        style.configure("Sub.TLabel", font=("Segoe UI", 10),
                        foreground=self.colors["muted"], background=self.colors["card"])
        style.configure("Muted.TLabel", font=("Segoe UI", 9),
                        foreground=self.colors["muted"], background=self.colors["card"])
        style.configure("TCheckbutton", background=self.colors["card"])

    def _build_ui(self):
        # Sombra
        shadow = tk.Frame(self, bg="#cdd6dd", bd=0)
        shadow.place(relx=0.5, rely=0.5, anchor="center", width=460, height=290, x=6, y=6)

        # Card
        card = ttk.Frame(self, style="Card.TFrame")
        card.place(relx=0.5, rely=0.5, anchor="center", width=460, height=290)

        header = ttk.Label(card, text="🔐 Bienvenido a Kiosko Pro", style="Header.TLabel")
        header.pack(pady=(18, 0))

        sub = ttk.Label(card, text="Ingresá tus credenciales para continuar", style="Sub.TLabel")
        sub.pack(pady=(4, 16))

        form = ttk.Frame(card, style="Card.TFrame")
        form.pack(padx=24, fill="x")

        # Usuario
        ttk.Label(form, text="Usuario", style="Muted.TLabel").pack(anchor="w")
        self.var_user = tk.StringVar()
        ent_user = ttk.Entry(form, textvariable=self.var_user, font=("Segoe UI", 10))
        ent_user.pack(fill="x", pady=(2, 10))
        ent_user.focus()

        # Password + toggle
        ttk.Label(form, text="Contraseña", style="Muted.TLabel").pack(anchor="w")
        self.var_pass = tk.StringVar()
        self.ent_pass = ttk.Entry(form, textvariable=self.var_pass, show="*", font=("Segoe UI", 10))
        self.ent_pass.pack(fill="x", pady=(2, 8))

        self.var_show = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(form, text="Mostrar contraseña", variable=self.var_show,
                              command=lambda: self.ent_pass.config(show="" if self.var_show.get() else "*"))
        chk.pack(anchor="w", pady=(0, 6))

        # Error (oculto inicialmente)
        self.lbl_error = ttk.Label(form, text="", style="Sub.TLabel",
                                   foreground="#e74c3c", background="#ffffff")
        self.lbl_error.pack(anchor="w")
        self._set_error("")

        # BOTÓN INGRESAR (tk.Button para asegurar colores en Windows)
        btn = tk.Button(card,
                        text="Ingresar",
                        font=("Segoe UI", 10, "bold"),
                        bg="#3498db", fg="white",
                        activebackground="#2d89c8", activeforeground="white",
                        relief="flat",
                        command=self._on_login)
        btn.pack(padx=24, fill="x", pady=(14, 0), ipady=6)

        # Footer
        ttk.Label(card, text="© Kiosko Pro", style="Muted.TLabel").pack(pady=(10, 0))

        # Enter = login
        self.bind("<Return>", lambda e: self._on_login())

    def _set_error(self, msg: str):
        self.lbl_error.configure(text=msg)

    def _on_login(self):
        usuario = (self.var_user.get() or "").strip()
        password = self.var_pass.get() or ""
        data = USUARIOS.get(usuario)

        if not data or data["password"] != password:
            self._set_error("Usuario o contraseña incorrectos.")
            self.shake()
            return

        # OK → abrir POS con permisos por rol
        rol = data["rol"]
        self.destroy()
        abrir_pos(usuario, rol)

    # Animación "shake"
    def shake(self):
        x = self.winfo_x()
        y = self.winfo_y()
        for dx in (8, -16, 12, -8, 4, -2, 0):
            self.geometry(f"+{x+dx}+{y}")
            self.update_idletasks()
            self.after(18)

# ─────────────────────────────────────────────────────────────────────
# Lanzadores
# ─────────────────────────────────────────────────────────────────────
def abrir_pos(usuario: str, rol: str):
    app = VentasAppConPermisos(usuario, rol)
    app.mainloop()

def abrir_login():
    LoginApp().mainloop()

# ─────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    LoginApp().mainloop()
