import os
import sys
import re
# ---- Variables globales ----
     # Tablas de comentarios
global tablaRegistros, tablaPares, tablaBits, tablaCondiciones
tablaRegistros = {'A':'111', 'B':'000', 'C':'001', 'D':'010', 'E':'011', 'H':'100', 'L':'101'}
tablaPares = {'BC':'00', 'DE':'01', 'HL':'10', 'SP':'11', 'AF':'11', 'IX':'10', 'IY':'10'}
tablaBits = {'0':'000', '1':'001', '2':'010', '3':'011', '4':'100', '5':'101', '6':'110', '7':'111'}
tablaCondiciones = {'NZ':'000', 'Z':'001', 'NC':'010', 'C':'011', 'PO':'100', 'PE':'101', 'P':'110', 'M':'111'}
      # Variables para traduccion
global tablaSimbolos, traduccion, cl
tablaSimbolos = {}
traduccion = ""
cl = 0

def validarArchivo(archivo):
    if not os.path.exists(archivo):
        raise Exception("Archivo no encontrado")
    if not archivo.endswith('.asm'):
        raise Exception("Archivo no es asm")

def crearLST(archivo):
    try:
        nombre = archivo.split('.')[0]+'.lst'
        with open(nombre, 'w') as f:
            f.write(traduccion)
    except:
        raise Exception("Error al crear archivo LST")

def agregarEtiqueta(simbolo):
    global tablaSimbolos
    if simbolo in tablaSimbolos.keys() and tablaSimbolos[simbolo] != simbolo:
        raise Exception(f'Declaracion duplicada del simbolo: {simbolo}')
    tablaSimbolos[simbolo] = hex(cl)[2:].zfill(4)

def buscarEtiqueta(simbolo):
    global tablaSimbolos
    if simbolo not in tablaSimbolos.keys():
        tablaSimbolos[simbolo] = f'__{simbolo}__'
    return tablaSimbolos[simbolo]

def validarMnemonico(linea):
    global cl
    if re.fullmatch(r'[l,L][d,D] [A,B,C,D,E,H,L,a,b,c,d,e,h,l], [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        cl += 1
        return hex(int(f'01{tablaRegistros[linea[3].upper()]}{tablaRegistros[linea[6].upper()]}', 2))[2:].upper()
    # Mnemonicos faltantes
    raise Exception("Mnemonico no reconocido: " + linea)

def pasada1(linea):
    global traduccion, cl
    linea = re.sub(r'\t+', ' ', linea) # Eliminar tabulaciones
    linea = re.sub(r' *, *', ', ', linea) # Eliminar espacios entre comas
    linea = re.sub(r' +', ' ', linea) # Eliminar espacios multiples
    linea = linea.strip() # Eliminar espacios al inicio y al final
    if re.fullmatch(r' ?\\n', linea) != None: # Linea vacia
        traduccion += "\n"
        return
    if re.fullmatch(r' ?;.*', linea) != None: # Comentario
        traduccion += linea.strip() + "\n"
        return
    if re.fullmatch(r' ?:.*', linea) != None: # No se da nombre a la etiqueta
        raise Exception("Error de syntaxis en la linea: " + linea)
    if re.fullmatch(r'.*:.*', linea) != None: # Se da nombre a la etiqueta
        if len(linea.split(':')) > 2: # Mas de una etiqueta en una linea
            raise Exception("Error de syntaxis en la linea: " + linea)
        agregarEtiqueta(linea.split(':')[0].strip())
        linea = linea.split(':')[1].strip()
    if re.fullmatch(r'.*;.*', linea) != None:
        mnemonico = linea.split(';')[0].strip()
        comentario = linea.split(';')[1].strip()
        traduccion += f'{hex(cl)[2:].zfill(4)}\t{validarMnemonico(mnemonico)}\t\t\t{comentario}\n'
        return
    traduccion += f'{hex(cl)[2:].zfill(4)}\t{validarMnemonico(linea)}\n'

def pasada2():
    for simbolo in tablaSimbolos.keys():
        if re.fullmatch(r'__.*__', tablaSimbolos[simbolo]) != None:
            raise Exception(f'Etiqueta no definida: {simbolo}')
        traduccion = re.sub(rf'__{simbolo}__', tablaSimbolos[simbolo], traduccion)
    
def agregarTS(archivo):
    with open(archivo, 'w') as f:
        for simbolo in tablaSimbolos.keys():
            f.write(f'{simbolo}\t{tablaSimbolos[simbolo]}\n')

if __name__ == "__main__":
    archivo = "prueba.asm"
    validarArchivo(archivo)
    with open(archivo, 'r') as f:
        for linea in f:
            pasada1(linea)
    pasada2(archivo)
    agregarTS(archivo)
    crearLST(archivo)