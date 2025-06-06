import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import io

# Configuración de la página
st.set_page_config(
    page_title="Progol Optimizer - Metodología Definitiva",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importar módulos locales con manejo de errores
try:
    from models.match_classifier import MatchClassifier
    from models.portfolio_generator import PortfolioGenerator
    from models.validators import PortfolioValidator
    from utils.helpers import (
        create_sample_data, 
        clean_for_json, 
        safe_json_dumps, 
        load_partidos_from_csv, 
        generate_csv_template, 
        validate_partido_data
    )
    from config import Config
except ImportError as e:
    st.error(f"❌ Error importando módulos: {str(e)}")
    st.error("Verifica que todos los archivos estén en su lugar correcto")
    st.stop()

def main():
    """Función principal de la aplicación"""
    
    st.title("🎯 Progol Optimizer - Metodología Definitiva")
    st.markdown("*Sistema avanzado de optimización basado en arquitectura Core + Satélites*")
    
    # Inicializar session state
    inicializar_session_state()
    
    # Sidebar para configuración
    configurar_sidebar()
    
    # Área principal con tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Entrada de Datos", "🎯 Generación", "📈 Resultados", "📄 Exportar"])
    
    with tab1:
        mostrar_entrada_datos()
    
    with tab2:
        mostrar_generacion()
    
    with tab3:
        mostrar_resultados()
    
    with tab4:
        mostrar_exportacion()

def inicializar_session_state():
    """Inicializa el estado de la sesión"""
    if 'partidos_regular' not in st.session_state:
        st.session_state.partidos_regular = []
    if 'partidos_revancha' not in st.session_state:
        st.session_state.partidos_revancha = []
    if 'config' not in st.session_state:
        st.session_state.config = {
            'num_quinielas': 20,
            'empates_min': 4,
            'empates_max': 6,
            'concentracion_general': 0.70,
            'concentracion_inicial': 0.60,
            'correlacion_target': -0.35,
            'seed': 42
        }

def configurar_sidebar():
    """Configura el sidebar con parámetros"""
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Información de la metodología
        st.info(f"📊 **{Config.APP_NAME}** v{Config.APP_VERSION}\n\n🎯 {Config.APP_DESCRIPTION}")
        
        # Botón para cargar datos de muestra
        if st.button("📝 Cargar Datos de Muestra", type="secondary"):
            sample_data = create_sample_data()
            st.session_state.partidos_regular = sample_data['partidos_regular'][:14]
            st.session_state.partidos_revancha = sample_data['partidos_revancha'][:7]
            st.success("✅ Datos de muestra cargados")
            st.rerun()
        
        # Parámetros principales
        num_quinielas = st.slider("Número de quinielas", 10, 35, 20, 1)
        empates_min = st.slider("Empates mínimos por quiniela", 3, 6, 4)
        empates_max = st.slider("Empates máximos por quiniela", 4, 7, 6)
        
        # Guardar en session state
        st.session_state.config.update({
            'num_quinielas': num_quinielas,
            'empates_min': empates_min,
            'empates_max': empates_max
        })
        
        # Mostrar distribución histórica
        with st.expander("📊 Distribución Histórica Progol"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Locales", f"{Config.DISTRIBUCION_HISTORICA['L']:.1%}")
            with col2:
                st.metric("Empates", f"{Config.DISTRIBUCION_HISTORICA['E']:.1%}")
            with col3:
                st.metric("Visitantes", f"{Config.DISTRIBUCION_HISTORICA['V']:.1%}")

def mostrar_entrada_datos():
    """Muestra la interfaz de entrada de datos"""
    st.header("Información de Partidos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚽ Partidos Regulares (14)")
        entrada_partidos_con_csv(st.session_state.partidos_regular, 'regular')
    
    with col2:
        st.subheader("🔄 Partidos Revancha (7)")
        entrada_partidos_con_csv(st.session_state.partidos_revancha, 'revancha')

def entrada_partidos_con_csv(partidos_list, tipo):
    """Interfaz para entrada de partidos con opción CSV"""
    
    tab1, tab2 = st.tabs(["✏️ Entrada Manual", "📄 Cargar CSV"])
    
    with tab1:
        entrada_manual(partidos_list, tipo)
    
    with tab2:
        entrada_csv(partidos_list, tipo)

def entrada_manual(partidos_list, tipo):
    """Entrada manual de partidos"""
    max_partidos = 14 if tipo == 'regular' else 7
    key_suffix = tipo
    
    with st.form(f"agregar_partido_{tipo}"):
        col1, col2 = st.columns(2)
        
        with col1:
            equipo_local = st.text_input("Equipo Local", key=f"local_{key_suffix}")
        with col2:
            equipo_visitante = st.text_input("Equipo Visitante", key=f"visit_{key_suffix}")
        
        # Probabilidades
        col1, col2, col3 = st.columns(3)
        with col1:
            prob_local = st.slider("Prob. Local (%)", 0, 100, 40, key=f"prob_l_{key_suffix}")
        with col2:
            prob_empate = st.slider("Prob. Empate (%)", 0, 100, 30, key=f"prob_e_{key_suffix}")
        with col3:
            prob_visitante = st.slider("Prob. Visitante (%)", 0, 100, 30, key=f"prob_v_{key_suffix}")
        
        # Factores contextuales
        es_final = st.checkbox("Es Final/Derby", key=f"final_{key_suffix}")
        
        submitted = st.form_submit_button("Agregar Partido")
        
        if submitted and equipo_local and equipo_visitante:
            # Normalizar probabilidades
            total_prob = prob_local + prob_empate + prob_visitante
            if total_prob > 0:
                partido = {
                    'local': equipo_local,
                    'visitante': equipo_visitante,
                    'prob_local': prob_local / total_prob,
                    'prob_empate': prob_empate / total_prob,
                    'prob_visitante': prob_visitante / total_prob,
                    'es_final': es_final,
                    'forma_diferencia': 0,
                    'lesiones_impact': 0
                }
                
                if len(partidos_list) < max_partidos:
                    partidos_list.append(partido)
                    st.success(f"✅ Partido agregado: {equipo_local} vs {equipo_visitante}")
                    st.rerun()
                else:
                    st.error(f"❌ Ya tienes {max_partidos} partidos {tipo}.")
    
    # Mostrar partidos existentes
    if partidos_list:
        st.subheader(f"Partidos ingresados ({len(partidos_list)}/{max_partidos})")
        
        for i, partido in enumerate(partidos_list):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.text(f"{partido['local']} vs {partido['visitante']}")
            with col2:
                st.text(f"L:{partido['prob_local']:.2f} E:{partido['prob_empate']:.2f} V:{partido['prob_visitante']:.2f}")
            with col3:
                if st.button("🗑️", key=f"del_{key_suffix}_{i}"):
                    partidos_list.pop(i)
                    st.rerun()

def entrada_csv(partidos_list, tipo):
    """Entrada de partidos desde CSV"""
    st.subheader(f"📄 Cargar partidos desde CSV ({tipo})")
    
    # Botón para descargar template
    col1, col2 = st.columns(2)
    
    with col1:
        template_csv = generate_csv_template(tipo)
        st.download_button(
            label="📥 Descargar Template CSV",
            data=template_csv,
            file_name=f"template_partidos_{tipo}.csv",
            mime="text/csv",
            help="Descarga este template, llénalo con tus datos y súbelo aquí"
        )
    
    with col2:
        uploaded_file = st.file_uploader(
            f"Subir CSV de partidos {tipo}",
            type=['csv'],
            key=f"csv_upload_{tipo}",
            help="Sube un archivo CSV con el formato del template"
        )
    
    if uploaded_file is not None:
        try:
            # Preview del archivo
            st.write("**Preview del archivo subido:**")
            preview_df = pd.read_csv(uploaded_file)
            st.dataframe(preview_df.head(), use_container_width=True)
            
            # Resetear puntero
            uploaded_file.seek(0)
            
            # Botón para confirmar carga
            if st.button(f"✅ Cargar {len(preview_df)} partidos", key=f"confirm_load_{tipo}"):
                partidos_cargados = load_partidos_from_csv(uploaded_file, tipo)
                
                # Actualizar session state
                if tipo == 'regular':
                    st.session_state.partidos_regular = partidos_cargados
                else:
                    st.session_state.partidos_revancha = partidos_cargados
                
                st.success(f"✅ {len(partidos_cargados)} partidos {tipo} cargados exitosamente")
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error cargando CSV: {str(e)}")
            st.info("Verifica que el archivo tenga el formato correcto del template")

def mostrar_generacion():
    """Muestra la interfaz de generación de portafolio"""
    st.header("Generación de Portafolio")
    
    if len(st.session_state.partidos_regular) >= 14:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 Generar Core (4)", type="primary", use_container_width=True):
                generar_quinielas_core()
        
        with col2:
            if st.button("🔄 Generar Satélites", use_container_width=True):
                generar_quinielas_satelites()
        
        with col3:
            if st.button("⚡ Optimizar GRASP", use_container_width=True):
                ejecutar_optimizacion_grasp()
        
        # Mostrar progreso
        if 'quinielas_core' in st.session_state:
            st.success(f"✅ Core: {len(st.session_state.quinielas_core)} quinielas generadas")
        
        if 'quinielas_satelites' in st.session_state:
            st.success(f"✅ Satélites: {len(st.session_state.quinielas_satelites)} quinielas generadas")
        
        if 'quinielas_final' in st.session_state:
            st.success(f"✅ Optimización: {len(st.session_state.quinielas_final)} quinielas finales")
    else:
        st.warning("⚠️ Necesitas ingresar al menos 14 partidos regulares para continuar.")

def generar_quinielas_core():
    """Genera las 4 quinielas core"""
    try:
        with st.spinner("🔄 Generando quinielas Core..."):
            classifier = MatchClassifier()
            generator = PortfolioGenerator()
            
            # Clasificar partidos
            partidos_clasificados = classifier.classify_matches(st.session_state.partidos_regular)
            
            # Generar quinielas core
            quinielas_core = generator.generate_core_quinielas(partidos_clasificados)
            
            st.session_state.partidos_clasificados = partidos_clasificados
            st.session_state.quinielas_core = quinielas_core
            
            st.success(f"✅ {len(quinielas_core)} quinielas Core generadas exitosamente")
            
    except Exception as e:
        st.error(f"❌ Error generando quinielas core: {str(e)}")

def generar_quinielas_satelites():
    """Genera quinielas satélites"""
    if 'quinielas_core' not in st.session_state:
        st.error("❌ Primero debes generar las quinielas Core")
        return
    
    try:
        with st.spinner("🔄 Generando quinielas Satélites..."):
            generator = PortfolioGenerator()
            config = st.session_state.config
            
            num_total = config['num_quinielas']
            num_satelites = num_total - 4  # Restar las 4 Core
            
            quinielas_satelites = generator.generate_satellite_quinielas(
                st.session_state.partidos_clasificados,
                st.session_state.quinielas_core,
                num_satelites
            )
            
            st.session_state.quinielas_satelites = quinielas_satelites
            
            st.success(f"✅ {len(quinielas_satelites)} quinielas satélites generadas")
            
    except Exception as e:
        st.error(f"❌ Error generando satélites: {str(e)}")

def ejecutar_optimizacion_grasp():
    """Ejecuta la optimización GRASP-Annealing"""
    if 'quinielas_core' not in st.session_state or 'quinielas_satelites' not in st.session_state:
        st.error("❌ Necesitas generar Core y Satélites primero")
        return
    
    try:
        with st.spinner("🔄 Ejecutando optimización GRASP..."):
            generator = PortfolioGenerator()
            validator = PortfolioValidator()
            
            # Combinar todas las quinielas
            todas_quinielas = st.session_state.quinielas_core + st.session_state.quinielas_satelites
            
            # Optimizar
            quinielas_optimizadas = generator.optimize_portfolio_grasp(
                todas_quinielas,
                st.session_state.partidos_clasificados
            )
            
            # Validar
            validacion = validator.validate_portfolio(quinielas_optimizadas)
            
            st.session_state.quinielas_final = quinielas_optimizadas
            st.session_state.validacion = validacion
            
            if validacion['es_valido']:
                st.success("✅ Optimización completada exitosamente")
            else:
                st.warning("⚠️ Optimización completada con advertencias")
                
    except Exception as e:
        st.error(f"❌ Error en optimización: {str(e)}")

def mostrar_resultados():
    """Muestra análisis de resultados"""
    st.header("Análisis de Resultados")
    
    if 'quinielas_final' not in st.session_state:
        st.info("💡 Genera las quinielas primero para ver los resultados")
        return
    
    quinielas = st.session_state.quinielas_final
    validacion = st.session_state.get('validacion', {})
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Quinielas", len(quinielas))
    with col2:
        empates_promedio = np.mean([q['resultados'].count('E') for q in quinielas])
        st.metric("Empates Promedio", f"{empates_promedio:.1f}")
    with col3:
        prob_11_plus = np.mean([q.get('prob_11_plus', 0) for q in quinielas])
        st.metric("Pr[≥11] Promedio", f"{prob_11_plus:.1%}")
    with col4:
        if validacion.get('es_valido'):
            st.metric("Validación", "✅ Válido")
        else:
            st.metric("Validación", "⚠️ Advertencias")
    
    # Tabla de quinielas
    if quinielas:
        st.subheader("Quinielas Generadas")
        
        # Crear DataFrame para mostrar
        data = []
        for i, quiniela in enumerate(quinielas):
            row = {'Quiniela': f'Q-{i+1}'}
            for j, resultado in enumerate(quiniela['resultados']):
                row[f'P{j+1}'] = resultado
            row['Empates'] = quiniela['resultados'].count('E')
            row['Prob≥11'] = f"{quiniela.get('prob_11_plus', 0):.1%}"
            data.append(row)
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

def mostrar_exportacion():
    """Muestra opciones de exportación"""
    st.header("Exportación de Resultados")
    
    if 'quinielas_final' not in st.session_state:
        st.info("💡 Genera las quinielas primero para poder exportar")
        return
    
    quinielas = st.session_state.quinielas_final
    partidos = st.session_state.partidos_regular
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Exportar CSV
        if st.button("📁 Generar CSV", use_container_width=True):
            csv_data = generar_csv_export(quinielas, partidos)
            st.download_button(
                label="📥 Descargar CSV",
                data=csv_data,
                file_name=f"progol_quinielas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        # Exportar JSON
        if st.button("📄 Generar JSON", use_container_width=True):
            try:
                json_data = {
                    'fecha_generacion': datetime.now().isoformat(),
                    'partidos': partidos,
                    'quinielas': quinielas,
                    'total_quinielas': len(quinielas)
                }
                
                # Limpiar datos para JSON
                json_data_clean = clean_for_json(json_data)
                json_string = safe_json_dumps(json_data_clean, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label="📥 Descargar JSON",
                    data=json_string,
                    file_name=f"progol_quinielas_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ Error generando JSON: {str(e)}")
    
    with col3:
        # Exportar formato Progol
        if st.button("🎯 Generar Formato Progol", use_container_width=True):
            progol_format = generar_formato_progol(quinielas)
            st.download_button(
                label="📥 Descargar Progol",
                data=progol_format,
                file_name=f"progol_boletos_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )

def generar_csv_export(quinielas, partidos):
    """Genera CSV para exportación"""
    output = io.StringIO()
    
    # Crear datos
    data = []
    for i, quiniela in enumerate(quinielas):
        row = {'Quiniela': f'Q-{i+1}'}
        for j, resultado in enumerate(quiniela['resultados']):
            row[f'Partido_{j+1}'] = resultado
        row['Empates'] = quiniela['resultados'].count('E')
        row['Prob_11_Plus'] = quiniela.get('prob_11_plus', 0)
        data.append(row)
    
    # Convertir a DataFrame y CSV
    df = pd.DataFrame(data)
    df.to_csv(output, index=False)
    
    return output.getvalue()

def generar_formato_progol(quinielas):
    """Genera formato específico para Progol"""
    output = []
    output.append("PROGOL OPTIMIZER - QUINIELAS GENERADAS")
    output.append("=" * 50)
    output.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    output.append(f"Total de quinielas: {len(quinielas)}")
    output.append("")
    
    for i, quiniela in enumerate(quinielas):
        output.append(f"QUINIELA {i+1:02d}: {' '.join(quiniela['resultados'])}")
    
    return "\n".join(output)

if __name__ == "__main__":
    main()