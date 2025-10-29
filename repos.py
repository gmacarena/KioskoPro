from typing import List, Dict, Optional, Any
from config import get_connection
import time 
# ----------------- Helpers -----------------
def _dict_rows(cur) -> List[Dict[str, Any]]:
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def _dict_one(cur) -> Optional[Dict[str, Any]]:
    row = cur.fetchone()
    if not row:
        return None
    cols = [c[0] for c in cur.description]
    return dict(zip(cols, row))

# ----------------- Categorías -----------------
# En repos.py, agregar estos métodos a la clase CategoriaRepo
class CategoriaRepo:
    @staticmethod
    def listar() -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, nombre, descripcion FROM categorias ORDER BY nombre")
            return _dict_rows(cur)
        finally:
            conn.close()

    @staticmethod
    def agregar(nombre: str, descripcion: str = None):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def actualizar(categoria_id: int, nombre: str, descripcion: str = None):
        """Actualizar una categoría existente"""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE categorias 
                SET nombre = ?, descripcion = ? 
                WHERE id = ?
            """, (nombre, descripcion, categoria_id))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def eliminar(categoria_id: int):
        """Eliminar una categoría (solo si no tiene productos)"""
        conn = get_connection()
        try:
            cur = conn.cursor()
            # Verificar si hay productos asociados
            cur.execute("SELECT COUNT(*) FROM productos WHERE categoria_id = ?", (categoria_id,))
            count = cur.fetchone()[0]
            
            if count > 0:
                raise Exception("No se puede eliminar la categoría porque tiene productos asociados")
            
            cur.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def buscar_por_id(categoria_id: int) -> Optional[Dict[str, Any]]:
        """Buscar categoría por ID específico"""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, nombre, descripcion FROM categorias WHERE id = ?", (categoria_id,))
            return _dict_one(cur)
        finally:
            conn.close()

# ----------------- Productos -----------------
class ProductoRepo:
    @staticmethod
    def listar() -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT p.id, p.codigo_barras, p.nombre, p.precio, p.stock, 
                       ISNULL(c.nombre,'') AS categoria, p.activo
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                ORDER BY p.nombre
            """)
            return _dict_rows(cur)
        finally:
            conn.close()

    @staticmethod
    def buscar(codigo_o_nombre: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, codigo_barras, nombre, precio, stock, activo
                FROM productos
                WHERE codigo_barras = ? OR nombre LIKE ?
            """, (codigo_o_nombre, f"%{codigo_o_nombre}%"))
            return _dict_one(cur)
        finally:
            conn.close()

    @staticmethod
    def buscar_por_id(producto_id: int) -> Optional[Dict[str, Any]]:
        """Buscar producto por ID específico"""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT p.id, p.codigo_barras, p.nombre, p.precio, p.stock, 
                       p.stock_minimo, p.proveedor, p.activo, p.categoria_id,
                       ISNULL(c.nombre, '') AS categoria
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE p.id = ?
            """, (producto_id,))
            return _dict_one(cur)
        except Exception as e:
            print(f"Error buscando producto por ID: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def buscar(codigo_o_nombre: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, codigo_barras, nombre, precio, stock, activo
                FROM productos
                WHERE codigo_barras = ? OR nombre LIKE ?
            """, (codigo_o_nombre, f"%{codigo_o_nombre}%"))
            return _dict_one(cur)
        finally:
            conn.close()

    @staticmethod
    def agregar(nombre, precio, stock, categoria_id=None, codigo=None):
        if not codigo:  # si no se pasa código, generar uno automático
            codigo = f"AUTO-{int(time.time())}"

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO productos (codigo_barras, nombre, precio, stock, categoria_id)
                VALUES (?, ?, ?, ?, ?)
            """, (codigo, nombre, precio, stock, categoria_id))
            conn.commit()

    @staticmethod
    def actualizar_precio(producto_id: int, nuevo_precio: float):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE productos SET precio = ?, fecha_modificacion = GETDATE() WHERE id = ?", (nuevo_precio, producto_id))
            conn.commit()
        finally:
            conn.close()

     
    @staticmethod
    def buscar_por_id(producto_id: int) -> Optional[Dict[str, Any]]:
        """Buscar producto por ID específico"""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, codigo_barras, nombre, precio, stock, activo
                FROM productos
                WHERE id = ?
            """, (producto_id,))
            return _dict_one(cur)
        finally:
            conn.close()
            
    @staticmethod
    def actualizar_completo(producto_id: int, nombre: str, precio: float, codigo_barras: str = None,
                          categoria_id: int = None, stock: int = None, stock_minimo: int = None,
                          proveedor: str = None, activo: bool = True):
        """Actualizar todos los campos de un producto"""
        conn = get_connection()
        try:
            cur = conn.cursor()
            
            # Construir la consulta dinámicamente
            campos = []
            valores = []
            
            if nombre is not None:
                campos.append("nombre = ?")
                valores.append(nombre)
            if precio is not None:
                campos.append("precio = ?")
                valores.append(precio)
            if codigo_barras is not None:
                campos.append("codigo_barras = ?")
                valores.append(codigo_barras)
            if categoria_id is not None:
                campos.append("categoria_id = ?")
                valores.append(categoria_id)
            if stock is not None:
                campos.append("stock = ?")
                valores.append(stock)
            if stock_minimo is not None:
                campos.append("stock_minimo = ?")
                valores.append(stock_minimo)
            if proveedor is not None:
                campos.append("proveedor = ?")
                valores.append(proveedor)
            if activo is not None:
                campos.append("activo = ?")
                valores.append(activo)
            
            # Agregar fecha de modificación
            campos.append("fecha_modificacion = GETDATE()")
            
            # Agregar ID al final
            valores.append(producto_id)
            
            if campos:
                query = f"UPDATE productos SET {', '.join(campos)} WHERE id = ?"
                cur.execute(query, valores)
                conn.commit()
                
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def actualizar_stock(producto_id: int, nuevo_stock: int):
        """Actualizar solo el stock de un producto"""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE productos 
                SET stock = ?, fecha_modificacion = GETDATE() 
                WHERE id = ?
            """, (nuevo_stock, producto_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def buscar_por_id(producto_id: int) -> Optional[Dict[str, Any]]:
        """Buscar producto por ID específico"""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT p.id, p.codigo_barras, p.nombre, p.precio, p.stock, 
                       p.stock_minimo, p.proveedor, p.activo, p.categoria_id,
                       ISNULL(c.nombre, '') AS categoria
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE p.id = ?
            """, (producto_id,))
            return _dict_one(cur)
        except Exception as e:
            print(f"Error buscando producto por ID: {e}")
            return None
        finally:
            conn.close()

class PuntoVentaRepo:
    @staticmethod
    def listar() -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, nombre, direccion, telefono FROM puntos_venta ORDER BY nombre")
            return _dict_rows(cur)
        finally:
            conn.close()

    @staticmethod
    def agregar(nombre: str, direccion: str, telefono: str):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO puntos_venta (nombre, direccion, telefono) VALUES (?, ?, ?)", (nombre, direccion, telefono))
            conn.commit()
        finally:
            conn.close()

class VentaRepo:
    @staticmethod
    def crear_venta(punto_venta_id: int, items: List[Dict[str, Any]], forma_pago="EFECTIVO", descuento=0.0) -> int:
        """
        Crea una venta con sus detalles, descuenta stock e inserta movimientos_stock.
        items = [{"producto_id":1,"nombre":"X","precio":100,"cantidad":2}, ...]
        """
        conn = get_connection()
        try:
            conn.autocommit = False
            cur = conn.cursor()

            subtotal = sum(it['cantidad'] * it['precio'] for it in items)
            total = round(subtotal * (1 - descuento/100.0), 2)

            cur.execute("""
                INSERT INTO ventas (fecha, total, descuento, forma_pago, punto_venta_id)
                OUTPUT INSERTED.id
                VALUES (GETDATE(), ?, ?, ?, ?)
            """, (total, descuento, forma_pago, punto_venta_id))
            venta_id = cur.fetchone()[0]

            for it in items:
                
                cur.execute("""
                    INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, precio_final, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (venta_id, it['producto_id'], it['cantidad'], it['precio'],
                      it['precio']*it['cantidad'], it['precio']*it['cantidad']))

           
                cur.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (it['cantidad'], it['producto_id']))

             
                cur.execute("""
                    INSERT INTO movimientos_stock (producto_id, tipo, cantidad, stock_anterior, stock_nuevo)
                    VALUES (?, 'VENTA', ?, 
                        (SELECT stock + ? FROM productos WHERE id=?),
                        (SELECT stock FROM productos WHERE id=?))
                """, (it['producto_id'], it['cantidad'], it['cantidad'], it['producto_id'], it['producto_id']))

            conn.commit()
            return venta_id
        except:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def listar(limit=50) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT TOP (?) id, fecha, total, forma_pago FROM ventas ORDER BY fecha DESC", (limit,))
            return _dict_rows(cur)
        finally:
            conn.close()
