import os
import sys
import re
# ---- Variables globales ----
     # Tablas de comentarios
global tablaRegistros, tablaPares, tablaBits, tablaCondiciones, palabrasReservadas
tablaRegistros = {'A':'111', 'B':'000', 'C':'001', 'D':'010', 'E':'011', 'H':'100', 'L':'101'}
tablaPares = {'BC':'00', 'DE':'01', 'HL':'10', 'SP':'11', 'AF':'11', 'IX':'10', 'IY':'10'}
tablaBits = {'0':'000', '1':'001', '2':'010', '3':'011', '4':'100', '5':'101', '6':'110', '7':'111'}
tablaCondiciones = {'NZ':'000', 'Z':'001', 'NC':'010', 'C':'011', 'PO':'100', 'PE':'101', 'P':'110', 'M':'111'}
palabrasReservadas = ['DEFMACRO', 'ENDMACRO']
      # Variables para traduccion
global tablaSimbolos, tablaMacros, traduccion, cl
tablaSimbolos = {}
tablaMacros = {} # {'nombre':{parametros:[], lineas:[]}
traduccion = []
cl = 0

def validarArchivo(archivo):
    if not os.path.exists(archivo):
        raise Exception("Archivo no encontrado")
    if not archivo.endswith('.asm'):
        raise Exception("Archivo no es asm")

def leerArchivo(archivo):
    validarArchivo(archivo)
    with open(archivo, 'r') as f:
        return f.read()

def formatoLinea(linea):
    indice = linea.find(';')
    codigo = linea[:indice] if indice != -1 else linea
    if len(codigo) == 0:
        return ['', linea[indice:] if indice != -1 else '']
    codigo = re.sub(r'\t+', ' ', codigo) # Eliminar tabulaciones
    codigo = re.sub(r' *, *', ', ', codigo) # Eliminar espacios entre comas
    codigo = re.sub(r' +', ' ', codigo) # Eliminar espacios multiples
    codigo = codigo.strip() # Eliminar espacios al inicio y al final
    if len(codigo) == 0:
        return ['', linea[indice:] if indice != -1 else '']
    if re.fullmatch(r'[a-zA-Z][a-zA-Z0-9 ,#:]*', codigo) == None:
        raise Exception("Error de syntaxis en la linea: " + linea)
    if codigo.count(':') > 1:
        raise Exception("Error de syntaxis en la linea: " + linea)
    return [codigo,f'{linea[indice:]}' if indice != -1 else '']

def crearLST(nombre):
    global traduccion
    lst = ''
    while True:
        if len(traduccion[0]) == 4:
            linea = traduccion.pop(0)
            lst += f'{linea[0]} {linea[1]}\t\t\t{linea[2]}\t\t\t{linea[3]}\n'
        else:
            break
    lst += f'\n{traduccion.pop(0)}\n'
    contador = 0
    while len(traduccion) != 0:
        if contador == 4:
            lst += '\n'
            contador = 0
        linea = traduccion.pop(0)
        lst += f'{linea}\t'
    
    with open(nombre.replace('.asm', '.lst'), 'w') as f:
        f.write(lst)

def agregarSimbolo(simbolo):
    global tablaSimbolos
    if simbolo in palabrasReservadas:
        raise Exception(f'Nombre de simbolo no puede ser palabra reservada: {simbolo}')
    if re.fullmatch(r'[a-zA-Z][a-zA-Z0-9]{0,10}', simbolo) == None:
        raise Exception(f'Nombre de simbolo invalido: {simbolo}')
    if simbolo in tablaSimbolos.keys():
        raise Exception(f'Declaracion duplicada del simbolo: {simbolo}')
    tablaSimbolos[simbolo] = hex(cl)[2:].zfill(4)

def buscarEtiqueta(simbolo):
    global tablaSimbolos
    if simbolo not in tablaSimbolos.keys():
        tablaSimbolos[simbolo] = f'__{simbolo}__'
    return tablaSimbolos[simbolo]

def macroEnsamble(archivo):
    global tablaMacros, traduccion
    macrosActivas = []
    archivoNuevo = []
    for linea in archivo.split('\n'): # Pasada 1
        linea = formatoLinea(linea)
        if re.fullmatch(r'DEFMACRO [a-zA-Z][a-zA-Z0-9]{0,10} ?:(( ?#[a-zA-Z][a-zA-Z0-9]{0,12},)* ?#[a-zA-Z][a-zA-Z0-9]{0,12})?', linea[0]) != None:
            nombre = linea[0].split(':')[0].split(' ')[1].strip()
            if nombre in palabrasReservadas:
                raise Exception(f'Nombre de macro no puede ser palabra reservada: {nombre}')
            if nombre in tablaMacros.keys():
                raise Exception(f'Definicio duplicada de macro: {nombre}')
            parametros = linea[0].split(':')[1].strip().split(',')
            parametros = [parametro.strip() for parametro in parametros]
            macrosActivas.append(nombre)
            tablaMacros[nombre] = {'parametros':parametros, 'lineas':[]}
            continue
        if re.fullmatch(r'ENDMACRO', linea[0]) != None:
            try:
                macrosActivas.pop()
            except:
                raise Exception(f'Se intento cerrar una macro sin haberla abierto: {linea}')
            continue
        if len(macrosActivas) != 0:
            for i in macrosActivas:
                tablaMacros[i]['lineas'].append(linea)
            continue
        archivoNuevo.append(linea)
    if len(macrosActivas) != 0:
        raise Exception(f'No se cerraon la(s) macro(s): {macrosActivas}')
    archivo = archivoNuevo.copy()
    # Pasada intermedia para reemplazar macros dentro de macros
    for macro in tablaMacros.keys():
        macroModificada = []
        for linea in tablaMacros[macro]['lineas']:
            if linea[0].count(':') == 1:
                nombreMacro = linea[0].split(':')[0].strip()
                if nombreMacro in tablaMacros.keys():
                    parametros = linea[0].split(':')[1].strip().split(',')
                    parametros = [parametro.strip() for parametro in parametros]
                    if len(parametros) != len(tablaMacros[nombreMacro]['parametros']):
                        raise Exception(f'Numero de parametros incorrecto en la llamada a la macro: {nombreMacro} se esperaban {len(tablaMacros[nombreMacro]["parametros"])}')
                    for lineaMacro in tablaMacros[nombreMacro]['lineas']:
                        nuevaLinea = lineaMacro.copy()
                        # validar que el numero de parametros sea el correcto
                        for i in range(len(parametros)):
                            nuevaLinea[0] = re.sub(f'{tablaMacros[nombreMacro]["parametros"][i]}', parametros[i], nuevaLinea[0])
                        macroModificada.append(nuevaLinea)
                else:
                    macroModificada.append(linea)
            else:
                macroModificada.append(linea)
        tablaMacros[macro]['lineas'] = macroModificada.copy()
    archivoNuevo = []
    for linea in archivo: # Pasada 2
        if len(linea[0]) == 0:
            archivoNuevo.append(linea)
            continue
        if linea[0].count(':') == 1:
            nombreMacro = linea[0].split(':')[0].strip()
            if nombreMacro in tablaMacros.keys():
                parametros = linea[0].split(':')[1].strip().split(',')
                parametros = [parametro.strip() for parametro in parametros]
                if len(parametros) != len(tablaMacros[nombreMacro]['parametros']):
                    raise Exception(f'Numero de parametros incorrecto en la llamada a la macro: {nombreMacro} se esperaban {len(tablaMacros[nombreMacro]["parametros"])}')
                for lineaMacro in tablaMacros[nombreMacro]['lineas']:
                    nuevaLinea = lineaMacro.copy()
                    # validar que el numero de parametros sea el correcto
                    for i in range(len(parametros)):
                        nuevaLinea[0] = re.sub(f'{tablaMacros[nombreMacro]["parametros"][i]}', parametros[i], nuevaLinea[0])
                    archivoNuevo.append(nuevaLinea)
            else:
                archivoNuevo.append(linea)
        else:
            archivoNuevo.append(linea)
    traduccion = archivoNuevo.copy()

def validarMnemonico(linea, pasada1 = True):
    global cl
    if re.fullmatch(r'[l,L][d,D] [A,B,C,D,E,H,L,a,b,c,d,e,h,l], [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'01{tablaRegistros[linea[3].upper()]}{tablaRegistros[linea[6].upper()]}', 2))[2:].upper()
    # Mnemonicos faltantes
    raise Exception("Mnemonico no reconocido: " + linea)

def pasada1():
    global traduccion
    nuevaTraduccion = []
    for linea in traduccion:
        if len(linea[0]) == 0:
            nuevaTraduccion.append(['','', '',linea[1]])
            continue
        if linea[0].count(':') == 1:
            nombre = linea[0].split(':')[0].strip()
            agregarSimbolo(nombre)
            if len(linea[0].split(':')[1].strip()) == 0:
                nuevaTraduccion.append([hex(cl)[2:].zfill(4).upper(), '', linea[0],linea[1]])
                continue
            nuevaTraduccion.append([hex(cl)[2:].zfil(4).upper(), validarMnemonico(linea[0].split(':')[1].strip()),linea[0].split(':')[1].strip(), linea[1]])
            continue
        nuevaTraduccion.append([hex(cl)[2:].zfill(4).upper(), validarMnemonico(linea[0]), linea[0], linea[1]])
    traduccion = nuevaTraduccion.copy()

def pasada2():
    global traduccion
    nuevaTraduccion = []
    for linea in traduccion:
        if len(linea[2]) == 0:
            nuevaTraduccion.append(linea)
            continue
        if len(linea[1]) == 0:
            if linea[2].count(':') == 1:
                nuevaTraduccion.append(linea)
                continue
            for simbolo in tablaSimbolos.keys():
                linea[2] = re.sub(simbolo, buscarEtiqueta(simbolo), linea[2])
            linea[1] = validarMnemonico(linea[2], False)
        nuevaTraduccion.append(linea)
    traduccion = nuevaTraduccion.copy()

def agregarTS():
    global traduccion
    traduccion.append('TABLA DE SIMBOLOS')
    for simbolo, dir in tablaSimbolos.items():
        traduccion.append(f'{simbolo} {dir}')

if __name__ == "__main__":
    nombre = "prueba.asm"
    archivo = leerArchivo(nombre)
    macroEnsamble(archivo)
    pasada1()
    pasada2()
    agregarTS()
    crearLST(nombre)