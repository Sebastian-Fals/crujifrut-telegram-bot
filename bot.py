import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    ConversationHandler,
    ContextTypes,
    filters
)
import os
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient import discovery
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Estados para las conversaciones
AWAITING_CLIENTE = 1
AWAITING_CANTIDAD = 2
AWAITING_VALOR = 3
AWAITING_DEUDA = 4
AWAITING_METODO_VENTA = 5

AWAITING_GASTO = 6
AWAITING_COSTO = 7
AWAITING_METODO_GASTO = 8

# Configurar Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    """Obtener el servicio de Google Sheets"""
    credentials = Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES)
    service = discovery.build('sheets', 'v4', credentials=credentials)
    return service

# ============ COMANDOS PRINCIPALES ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start - Mostrar menú principal"""
    keyboard = [
        ['➕ Agregar Compra', '💸 Agregar Gasto'],
        ['📊 Ver Total de Ventas', '📉 Ver Total de Gastos'],
        ['📋 Ver Balance'],
        ['👥 Resumen Clientes', '💰 Resumen Gastos'],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "¡Bienvenido! Soy tu bot de control de gastos y ganancias.\n\n"
        "¿Qué deseas hacer?",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /help - Mostrar ayuda"""
    help_text = """
*Comandos disponibles:*

/start - Mostrar menú principal
/help - Mostrar esta ayuda
/nuevaventa - Agregar una nueva venta
/nuevogasto - Agregar un nuevo gasto
/totventas - Ver total de ventas
/totgastos - Ver total de gastos
/balance - Ver balance final
/resumen - Ver resumen de clientes
/cliente <nombre> - Ver detalles de un cliente
/resumen_gastos - Ver resumen de gastos
/gasto <descripción> - Ver detalles de un gasto
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ============ AGREGAR COMPRA/VENTA ============

async def agregar_compra(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Iniciar el proceso de agregar una compra"""
    await update.message.reply_text(
        "📝 *Nuevo Registro de Venta*\n\n"
        "¿Cuál es el nombre del cliente?",
        parse_mode='Markdown'
    )
    return AWAITING_CLIENTE

async def recibir_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibir nombre del cliente"""
    context.user_data['cliente'] = update.message.text
    await update.message.reply_text("¿Qué cantidad se vendió?")
    return AWAITING_CANTIDAD

async def recibir_cantidad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibir cantidad"""
    try:
        context.user_data['cantidad'] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Por favor, ingresa un número válido")
        return AWAITING_CANTIDAD
    
    await update.message.reply_text("¿Cuál es el valor a pagar?")
    return AWAITING_VALOR

async def recibir_valor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibir valor a pagar"""
    try:
        context.user_data['valor'] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Por favor, ingresa un número válido")
        return AWAITING_VALOR
    
    await update.message.reply_text("¿Cuál es el monto de deuda? (si no hay, escribe 0)")
    return AWAITING_DEUDA

async def recibir_deuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibir deuda"""
    try:
        context.user_data['deuda'] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Por favor, ingresa un número válido")
        return AWAITING_DEUDA
    
    keyboard = [['Nequi', 'Efectivo']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "¿Cuál es el método de pago?",
        reply_markup=reply_markup
    )
    return AWAITING_METODO_VENTA

async def recibir_metodo_venta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibir método de pago y guardar en Google Sheets"""
    metodo = update.message.text
    
    if metodo not in ['Nequi', 'Efectivo']:
        keyboard = [['Nequi', 'Efectivo']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "❌ Por favor, selecciona Nequi o Efectivo",
            reply_markup=reply_markup
        )
        return AWAITING_METODO_VENTA
    
    context.user_data['metodo'] = metodo
    
    # Guardar en Google Sheets
    try:
        service = get_sheets_service()
        
        fecha = datetime.now().strftime("%d/%m/%Y")
        valores = [[
            context.user_data['cliente'],
            fecha,
            context.user_data['cantidad'],
            context.user_data['valor'],
            context.user_data['deuda'],
            metodo
        ]]
        
        body = {'values': valores}
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Ventas!A2',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        await update.message.reply_text(
            f"✅ *Venta registrada correctamente*\n\n"
            f"Cliente: {context.user_data['cliente']}\n"
            f"Cantidad: {context.user_data['cantidad']}\n"
            f"Valor: ${context.user_data['valor']}\n"
            f"Deuda: ${context.user_data['deuda']}\n"
            f"Método: {metodo}",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        
    except Exception as e:
        logger.error(f"Error al guardar en Google Sheets: {e}")
        await update.message.reply_text(
            f"❌ Error al guardar: {str(e)}",
            reply_markup=ReplyKeyboardRemove()
        )
    
    # Mostrar menú principal
    await start(update, context)
    return ConversationHandler.END

# ============ AGREGAR GASTO ============

async def agregar_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Iniciar el proceso de agregar un gasto"""
    await update.message.reply_text(
        "📝 *Nuevo Registro de Gasto*\n\n"
        "¿Cuál es la descripción del gasto?",
        parse_mode='Markdown'
    )
    return AWAITING_GASTO

async def recibir_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibir descripción del gasto"""
    context.user_data['gasto'] = update.message.text
    await update.message.reply_text("¿Cuál es el costo?")
    return AWAITING_COSTO

async def recibir_costo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibir costo del gasto"""
    try:
        context.user_data['costo'] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Por favor, ingresa un número válido")
        return AWAITING_COSTO
    
    keyboard = [['Nequi', 'Efectivo']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "¿Cuál es el método de pago?",
        reply_markup=reply_markup
    )
    return AWAITING_METODO_GASTO

async def recibir_metodo_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibir método de pago del gasto y guardar"""
    metodo = update.message.text
    
    if metodo not in ['Nequi', 'Efectivo']:
        keyboard = [['Nequi', 'Efectivo']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "❌ Por favor, selecciona Nequi o Efectivo",
            reply_markup=reply_markup
        )
        return AWAITING_METODO_GASTO
    
    context.user_data['metodo'] = metodo
    
    # Guardar en Google Sheets
    try:
        service = get_sheets_service()
        
        valores = [[
            context.user_data['gasto'],
            context.user_data['costo'],
            metodo
        ]]
        
        body = {'values': valores}
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Gastos!A2',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        await update.message.reply_text(
            f"✅ *Gasto registrado correctamente*\n\n"
            f"Gasto: {context.user_data['gasto']}\n"
            f"Costo: ${context.user_data['costo']}\n"
            f"Método: {metodo}",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        
    except Exception as e:
        logger.error(f"Error al guardar en Google Sheets: {e}")
        await update.message.reply_text(
            f"❌ Error al guardar: {str(e)}",
            reply_markup=ReplyKeyboardRemove()
        )
    
    # Mostrar menú principal
    await start(update, context)
    return ConversationHandler.END

# ============ VER TOTALES ============

async def ver_total_ventas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ver el total de ventas"""
    try:
        service = get_sheets_service()
        
        # Leer datos de la pestaña Ventas
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Ventas!A:F'
        ).execute()
        
        rows = result.get('values', [])[1:]  # Saltar encabezado
        
        if not rows:
            await update.message.reply_text("📊 No hay ventas registradas aún")
            return
        
        total_ventas = 0
        nequi_total = 0
        efectivo_total = 0
        
        for row in rows:
            try:
                valor = float(row[3]) if len(row) > 3 else 0
                metodo = row[5] if len(row) > 5 else ""
                
                total_ventas += valor
                
                if metodo == "Nequi":
                    nequi_total += valor
                elif metodo == "Efectivo":
                    efectivo_total += valor
                    
            except (ValueError, IndexError):
                continue
        
        mensaje = (
            f"📊 *Total de Ventas*\n\n"
            f"💰 Total: ${total_ventas:,.2f}\n"
            f"📱 Nequi: ${nequi_total:,.2f}\n"
            f"💵 Efectivo: ${efectivo_total:,.2f}\n"
            f"📈 Registros: {len(rows)}"
        )
        
        await update.message.reply_text(mensaje, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error al leer ventas: {e}")
        await update.message.reply_text(f"❌ Error al obtener datos: {str(e)}")

async def ver_total_gastos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ver el total de gastos"""
    try:
        service = get_sheets_service()
        
        # Leer datos de la pestaña Gastos
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Gastos!A:C'
        ).execute()
        
        rows = result.get('values', [])[1:]  # Saltar encabezado
        
        if not rows:
            await update.message.reply_text("📉 No hay gastos registrados aún")
            return
        
        total_gastos = 0
        nequi_total = 0
        efectivo_total = 0
        
        for row in rows:
            try:
                costo = float(row[1]) if len(row) > 1 else 0
                metodo = row[2] if len(row) > 2 else ""
                
                total_gastos += costo
                
                if metodo == "Nequi":
                    nequi_total += costo
                elif metodo == "Efectivo":
                    efectivo_total += costo
                    
            except (ValueError, IndexError):
                continue
        
        mensaje = (
            f"📉 *Total de Gastos*\n\n"
            f"💰 Total: ${total_gastos:,.2f}\n"
            f"📱 Nequi: ${nequi_total:,.2f}\n"
            f"💵 Efectivo: ${efectivo_total:,.2f}\n"
            f"📈 Registros: {len(rows)}"
        )
        
        await update.message.reply_text(mensaje, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error al leer gastos: {e}")
        await update.message.reply_text(f"❌ Error al obtener datos: {str(e)}")

async def ver_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ver el balance (ganancias - gastos)"""
    try:
        service = get_sheets_service()
        
        # Leer ventas
        result_ventas = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Ventas!A:F'
        ).execute()
        
        # Leer gastos
        result_gastos = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Gastos!A:C'
        ).execute()
        
        rows_ventas = result_ventas.get('values', [])[1:]
        rows_gastos = result_gastos.get('values', [])[1:]
        
        total_ventas = 0
        total_gastos = 0
        
        # Calcular total de ventas
        for row in rows_ventas:
            try:
                valor = float(row[3]) if len(row) > 3 else 0
                total_ventas += valor
            except (ValueError, IndexError):
                continue
        
        # Calcular total de gastos
        for row in rows_gastos:
            try:
                costo = float(row[1]) if len(row) > 1 else 0
                total_gastos += costo
            except (ValueError, IndexError):
                continue
        
        balance = total_ventas - total_gastos
        emoji = "📈" if balance >= 0 else "📉"
        
        mensaje = (
            f"{emoji} *Balance General*\n\n"
            f"📊 Ventas Totales: ${total_ventas:,.2f}\n"
            f"📉 Gastos Totales: ${total_gastos:,.2f}\n"
            f"💰 *Balance: ${balance:,.2f}*"
        )
        
        await update.message.reply_text(mensaje, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error al calcular balance: {e}")
        await update.message.reply_text(f"❌ Error al obtener datos: {str(e)}")

# ============ VER RESUMEN POR CLIENTES ============

async def ver_resumen_clientes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ver resumen de todos los clientes"""
    try:
        service = get_sheets_service()
        
        # Leer datos de la pestaña Ventas
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Ventas!A:F'
        ).execute()
        
        rows = result.get('values', [])[1:]  # Saltar encabezado
        
        if not rows:
            await update.message.reply_text("📊 No hay ventas registradas aún")
            return
        
        # Agrupar por cliente
        clientes = {}
        
        for row in rows:
            try:
                cliente = row[0] if len(row) > 0 else "Desconocido"
                cantidad = float(row[2]) if len(row) > 2 else 0
                valor = float(row[3]) if len(row) > 3 else 0
                
                if cliente not in clientes:
                    clientes[cliente] = {'cantidad': 0, 'valor': 0, 'transacciones': 0}
                
                clientes[cliente]['cantidad'] += cantidad
                clientes[cliente]['valor'] += valor
                clientes[cliente]['transacciones'] += 1
                
            except (ValueError, IndexError):
                continue
        
        if not clientes:
            await update.message.reply_text("📊 No hay datos de clientes")
            return
        
        # Crear tabla
        tabla = "👥 *RESUMEN DE CLIENTES*\n\n"
        tabla += "```"
        tabla += f"{'Cliente':<20} {'Cantidad':<12} {'Total $':<15} {'Trans.':<6}\n"
        tabla += "─" * 53 + "\n"
        
        total_cantidad = 0
        total_valor = 0
        total_trans = 0
        
        for cliente in sorted(clientes.keys()):
            datos = clientes[cliente]
            tabla += f"{cliente:<20} {datos['cantidad']:>11.2f} ${datos['valor']:>13,.2f} {datos['transacciones']:>5}\n"
            
            total_cantidad += datos['cantidad']
            total_valor += datos['valor']
            total_trans += datos['transacciones']
        
        tabla += "─" * 53 + "\n"
        tabla += f"{'TOTAL':<20} {total_cantidad:>11.2f} ${total_valor:>13,.2f} {total_trans:>5}\n"
        tabla += "```"
        
        tabla += f"\n*Para ver detalles de un cliente usa: /cliente nombre*"
        
        await update.message.reply_text(tabla, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error al leer clientes: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ============ VER DETALLES DE UN CLIENTE ============

async def ver_cliente_detalle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ver detalles completos de un cliente específico"""
    if not context.args:
        await update.message.reply_text(
            "❌ *Uso:* `/cliente nombre`\n\n"
            "*Ejemplo:* `/cliente Santiago`",
            parse_mode='Markdown'
        )
        return
    
    nombre_cliente = " ".join(context.args)
    
    try:
        service = get_sheets_service()
        
        # Leer datos de Ventas
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Ventas!A:F'
        ).execute()
        
        rows = result.get('values', [])[1:]  # Saltar encabezado
        
        # Filtrar por cliente
        transacciones = []
        total_cantidad = 0
        total_valor = 0
        total_deuda = 0
        
        for row in rows:
            try:
                cliente = row[0] if len(row) > 0 else ""
                
                if cliente.lower() == nombre_cliente.lower():
                    fecha = row[1] if len(row) > 1 else "N/A"
                    cantidad = float(row[2]) if len(row) > 2 else 0
                    valor = float(row[3]) if len(row) > 3 else 0
                    deuda = float(row[4]) if len(row) > 4 else 0
                    metodo = row[5] if len(row) > 5 else "N/A"
                    
                    transacciones.append({
                        'fecha': fecha,
                        'cantidad': cantidad,
                        'valor': valor,
                        'deuda': deuda,
                        'metodo': metodo
                    })
                    
                    total_cantidad += cantidad
                    total_valor += valor
                    total_deuda += deuda
                    
            except (ValueError, IndexError):
                continue
        
        if not transacciones:
            await update.message.reply_text(f"❌ No hay ventas registradas para: *{nombre_cliente}*", parse_mode='Markdown')
            return
        
        # Crear reporte detallado
        reporte = f"👤 *DETALLES DE {nombre_cliente.upper()}*\n\n"
        reporte += "```"
        reporte += f"{'Fecha':<12} {'Cantidad':<12} {'Valor':<14} {'Deuda':<12} {'Método':<10}\n"
        reporte += "─" * 60 + "\n"
        
        for trans in transacciones:
            reporte += f"{str(trans['fecha']):<12} {trans['cantidad']:>11.2f} ${trans['valor']:>12,.2f} ${trans['deuda']:>10,.2f} {str(trans['metodo']):<10}\n"
        
        reporte += "─" * 60 + "\n"
        reporte += f"{'TOTAL':<12} {total_cantidad:>11.2f} ${total_valor:>12,.2f} ${total_deuda:>10,.2f}\n"
        reporte += "```"
        
        # Agregar resumen
        reporte += f"\n📊 *Información del Cliente:*\n"
        reporte += f"• Transacciones: {len(transacciones)}\n"
        reporte += f"• Cantidad Total: {total_cantidad:,.2f}\n"
        reporte += f"• Valor Total: ${total_valor:,.2f}\n"
        reporte += f"• Deuda Pendiente: ${total_deuda:,.2f}"
        
        await update.message.reply_text(reporte, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error al leer cliente: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ============ VER RESUMEN DE GASTOS (NUEVO) ============

async def ver_resumen_gastos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ver resumen de todos los gastos agrupados por descripción"""
    try:
        service = get_sheets_service()
        
        # Leer datos de la pestaña Gastos
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Gastos!A:C'
        ).execute()
        
        rows = result.get('values', [])[1:]  # Saltar encabezado
        
        if not rows:
            await update.message.reply_text("📉 No hay gastos registrados aún")
            return
        
        # Agrupar por descripción de gasto
        gastos = {}
        
        for row in rows:
            try:
                descripcion = row[0] if len(row) > 0 else "Desconocido"
                costo = float(row[1]) if len(row) > 1 else 0
                metodo = row[2] if len(row) > 2 else "N/A"
                
                if descripcion not in gastos:
                    gastos[descripcion] = {'costo': 0, 'cantidad': 0, 'nequi': 0, 'efectivo': 0}
                
                gastos[descripcion]['costo'] += costo
                gastos[descripcion]['cantidad'] += 1
                
                if metodo == "Nequi":
                    gastos[descripcion]['nequi'] += costo
                elif metodo == "Efectivo":
                    gastos[descripcion]['efectivo'] += costo
                
            except (ValueError, IndexError):
                continue
        
        if not gastos:
            await update.message.reply_text("📉 No hay datos de gastos")
            return
        
        # Crear tabla
        tabla = "💸 *RESUMEN DE GASTOS*\n\n"
        tabla += "```"
        tabla += f"{'Descripción':<20} {'Cantidad':<10} {'Total $':<15}\n"
        tabla += "─" * 45 + "\n"
        
        total_gastos = 0
        total_cantidad = 0
        
        for desc in sorted(gastos.keys()):
            datos = gastos[desc]
            tabla += f"{desc:<20} {datos['cantidad']:>9} ${datos['costo']:>13,.2f}\n"
            
            total_gastos += datos['costo']
            total_cantidad += datos['cantidad']
        
        tabla += "─" * 45 + "\n"
        tabla += f"{'TOTAL':<20} {total_cantidad:>9} ${total_gastos:>13,.2f}\n"
        tabla += "```"
        
        tabla += f"\n*Para ver detalles de un gasto usa: /gasto descripción*"
        
        await update.message.reply_text(tabla, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error al leer gastos: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ============ VER DETALLES DE UN GASTO (NUEVO) ============

async def ver_gasto_detalle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ver detalles completos de un gasto específico"""
    if not context.args:
        await update.message.reply_text(
            "❌ *Uso:* `/gasto descripción`\n\n"
            "*Ejemplo:* `/gasto Arriendo`",
            parse_mode='Markdown'
        )
        return
    
    descripcion_gasto = " ".join(context.args)
    
    try:
        service = get_sheets_service()
        
        # Leer datos de Gastos
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Gastos!A:C'
        ).execute()
        
        rows = result.get('values', [])[1:]  # Saltar encabezado
        
        # Filtrar por descripción
        registros = []
        total_costo = 0
        nequi_total = 0
        efectivo_total = 0
        
        for i, row in enumerate(rows):
            try:
                descripcion = row[0] if len(row) > 0 else ""
                
                if descripcion.lower() == descripcion_gasto.lower():
                    costo = float(row[1]) if len(row) > 1 else 0
                    metodo = row[2] if len(row) > 2 else "N/A"
                    
                    registros.append({
                        'numero': i + 1,
                        'costo': costo,
                        'metodo': metodo
                    })
                    
                    total_costo += costo
                    
                    if metodo == "Nequi":
                        nequi_total += costo
                    elif metodo == "Efectivo":
                        efectivo_total += costo
                    
            except (ValueError, IndexError):
                continue
        
        if not registros:
            await update.message.reply_text(f"❌ No hay gastos registrados para: *{descripcion_gasto}*", parse_mode='Markdown')
            return
        
        # Crear reporte detallado
        reporte = f"💰 *DETALLES DE GASTO: {descripcion_gasto.upper()}*\n\n"
        reporte += "```"
        reporte += f"{'#':<4} {'Costo':<15} {'Método':<12}\n"
        reporte += "─" * 31 + "\n"
        
        for reg in registros:
            reporte += f"{reg['numero']:<4} ${reg['costo']:>13,.2f} {str(reg['metodo']):<12}\n"
        
        reporte += "─" * 31 + "\n"
        reporte += f"{'TOTAL':<4} ${total_costo:>13,.2f}\n"
        reporte += "```"
        
        # Agregar resumen
        reporte += f"\n📊 *Información del Gasto:*\n"
        reporte += f"• Registros: {len(registros)}\n"
        reporte += f"• Costo Total: ${total_costo:,.2f}\n"
        reporte += f"• Nequi: ${nequi_total:,.2f}\n"
        reporte += f"• Efectivo: ${efectivo_total:,.2f}"
        
        await update.message.reply_text(reporte, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error al leer gasto: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ============ MANEJADOR DE BOTONES ============

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Manejar los clics de los botones"""
    texto = update.message.text
    
    if texto == '➕ Agregar Compra':
        return await agregar_compra(update, context)
    elif texto == '💸 Agregar Gasto':
        return await agregar_gasto(update, context)
    elif texto == '📊 Ver Total de Ventas':
        await ver_total_ventas(update, context)
        await start(update, context)
        return ConversationHandler.END
    elif texto == '📉 Ver Total de Gastos':
        await ver_total_gastos(update, context)
        await start(update, context)
        return ConversationHandler.END
    elif texto == '📋 Ver Balance':
        await ver_balance(update, context)
        await start(update, context)
        return ConversationHandler.END
    elif texto == '👥 Resumen Clientes':
        await ver_resumen_clientes(update, context)
        await start(update, context)
        return ConversationHandler.END
    elif texto == '💰 Resumen Gastos':
        await ver_resumen_gastos(update, context)
        await start(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Opción no reconocida. Por favor, usa los botones del menú")
        return ConversationHandler.END

# ============ CANCELAR CONVERSACIÓN ============

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancelar una conversación"""
    await update.message.reply_text(
        "❌ Operación cancelada",
        reply_markup=ReplyKeyboardRemove()
    )
    await start(update, context)
    return ConversationHandler.END

# ============ MAIN - CONFIGURAR EL BOT ============

def main():
    """Iniciar el bot"""
    print("🤖 Iniciando bot de gastos y ganancias...")
    
    # Crear aplicación
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Conversación para agregar compra
    conv_handler_compra = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^➕ Agregar Compra$'), agregar_compra),
            CommandHandler('nuevaventa', agregar_compra)
        ],
        states={
            AWAITING_CLIENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cliente)],
            AWAITING_CANTIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cantidad)],
            AWAITING_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_valor)],
            AWAITING_DEUDA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_deuda)],
            AWAITING_METODO_VENTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_metodo_venta)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Conversación para agregar gasto
    conv_handler_gasto = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^💸 Agregar Gasto$'), agregar_gasto),
            CommandHandler('nuevogasto', agregar_gasto)
        ],
        states={
            AWAITING_GASTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_gasto)],
            AWAITING_COSTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_costo)],
            AWAITING_METODO_GASTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_metodo_gasto)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Agregar handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('totventas', ver_total_ventas))
    app.add_handler(CommandHandler('totgastos', ver_total_gastos))
    app.add_handler(CommandHandler('balance', ver_balance))
    app.add_handler(CommandHandler('resumen', ver_resumen_clientes))
    app.add_handler(CommandHandler('cliente', ver_cliente_detalle))
    app.add_handler(CommandHandler('resumen_gastos', ver_resumen_gastos))
    app.add_handler(CommandHandler('gasto', ver_gasto_detalle))
    
    # Handlers de conversación
    app.add_handler(conv_handler_compra)
    app.add_handler(conv_handler_gasto)
    
    # Handler general para botones
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_buttons
    ))
    
    # Iniciar el bot
    print("✅ Bot iniciado. Presiona Ctrl+C para detener")
    app.run_polling()

if __name__ == '__main__':
    main()
