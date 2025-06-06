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

# Importar módulos locales
try:
    from models.match_classifier import MatchClassifier
    from models.portfolio_generator import PortfolioGenerator
    from models.validators import PortfolioValidator
    from utils.helpers import load_historical_data, export_quinielas, create_sample_data
    from config import Config
except ImportError as e:
    st.error(f"Error: No se pudieron importar los módulos: {str(e)}")
    st.error("Asegúrate de que todos los archivos estén en su lugar y que la estructura de carpetas sea correcta.")
    st.stop()

def main():
    st.title("🎯 Progol Optimizer - Metodología Definitiva")
    st.markdown("*Sistema avanzado de optimización basado en arquitectura Core + Satélites*")
    
    # Sidebar para configuración
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
        num_quinielas = st.slider(
            "Número de quinielas", 
            min_value=Config.INTERFAZ['num_quinielas_min'], 
            max_value=Config.INTERFAZ['num_quinielas_max'], 
            value=Config.INTERFAZ['num_quinielas_default'], 
            step=1
        )
        empates_min = st.slider(
            "Empates mínimos por quiniela", 
            min_value=3, 
            max_value=Config.EMPATES_MAX, 
            value=Config.EMPATES_MIN
        )
        empates_max = st.slider(
            "Empates máximos por quiniela", 
            min_value=Config.EMPATES_MIN, 
            max_value=7, 
            value=Config.EMPATES_MAX
        )
        
        # Límites de concentración
        st.subheader("Límites de concentración")
        concentracion_general = st.slider(
            "Concentración máxima general (%)", 
            min_value=60, 
            max_value=80, 
            value=int(Config.CONCENTRACION_MAX_GENERAL * 100)
        )
        concentracion_inicial = st.slider(
            "Concentración máxima partidos 1-3 (%)", 
            min_value=50, 
            max_value=70, 
            value=int(Config.CONCENTRACION_MAX_INICIAL * 100)
        )
        
        # Configuración avanzada
        with st.expander("Configuración avanzada"):
            correlacion_target = st.slider(
                "Correlación negativa objetivo", 
                min_value=-0.5, 
                max_value=-0.2, 
                value=Config.ARQUITECTURA['correlacion_objetivo'], 
                step=0.05
            )
            seed = st.number_input("Semilla aleatoria", min_value=1, max_value=1000, value=42)
            
        # Mostrar distribución histórica
        with st.expander("📊 Distribución Histórica Progol"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Locales", f"{Config.DISTRIBUCION_HISTORICA['L']:.1%}")
            with col2:
                st.metric("Empates", f"{Config.DISTRIBUCION_HISTORICA['E']:.1%}")
            with col3:
                st.metric("Visitantes", f"{Config.DISTRIBUCION_HISTORICA['V']:.1%}")
            
            st.caption(f"Promedio histórico: {Config.EMPATES_PROMEDIO_HISTORICO} empates por quiniela")
        
        # Guardar configuración en session state
        st.session_state.config = {
            'num_quinielas': num_quinielas,
            'empates_min': empates_min,
            'empates_max': empates_max,
            'concentracion_general': concentracion_general / 100,
            'concentracion_inicial': concentracion_inicial / 100,
            'correlacion_target': correlacion_target,
            'seed': seed
        }
    
    # Área principal
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Entrada de Datos", "🎯 Generación", "📈 Resultados", "📄 Exportar"])
    
    with tab1:
        st.header("Información de Partidos")
        
        # Inicializar session state para partidos
        if 'partidos_regular' not in st.session_state:
            st.session_state.partidos_regular = []
        if 'partidos_revancha' not in st.session_state:
            st.session_state.partidos_revancha = []
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚽ Partidos Regulares (14)")
            entrada_partidos_regular(st.session_state.partidos_regular)
        
        with col2:
            st.subheader("🔄 Partidos Revancha (7)")
            entrada_partidos_revancha(st.session_state.partidos_revancha)
    
    with tab2:
        st.header("Generación de Portafolio")
        
        if len(st.session_state.partidos_regular) >= 14:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                generar_core = st.button("🎯 Generar Core (4)", type="primary", use_container_width=True)
            with col2:
                generar_satelites = st.button("🔄 Generar Satélites", use_container_width=True)
            with col3:
                optimizar_portafolio = st.button("⚡ Optimizar GRASP", use_container_width=True)
            
            # Mostrar configuración actual
            if 'config' in st.session_state:
                with st.expander("📋 Configuración Actual"):
                    config = st.session_state.config
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Quinielas", config['num_quinielas'])
                        st.metric("Empates Min", config['empates_min'])
                    with col2:
                        st.metric("Empates Max", config['empates_max'])
                        st.metric("Concentración", f"{config['concentracion_general']:.0%}")
                    with col3:
                        st.metric("Correlación", f"{config['correlacion_target']:.2f}")
                        st.metric("Semilla", config['seed'])
            
            # Proceso de generación
            if generar_core:
                generar_quinielas_core()
            
            if generar_satelites:
                generar_quinielas_satelites()
            
            if optimizar_portafolio:
                ejecutar_optimizacion_grasp()
        else:
            st.warning("⚠️ Necesitas ingresar al menos 14 partidos regulares para continuar.")
    
    with tab3:
        st.header("Análisis de Resultados")
        mostrar_resultados()
    
    with tab4:
        st.header("Exportación")
        if 'quinielas_final' in st.session_state:
            exportar_resultados()
        else:
            st.info("Genera las quinielas primero para poder exportar.")

def entrada_partidos_regular(partidos_list):
    """Interfaz para ingresar partidos regulares"""
    
    # Formulario para agregar partido
    with st.form("agregar_partido_regular"):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            equipo_local = st.text_input("Equipo Local", key="local_reg")
        with col2:
            equipo_visitante = st.text_input("Equipo Visitante", key="visit_reg")
        with col3:
            submitted = st.form_submit_button("Agregar")
        
        # Probabilidades
        col1, col2, col3 = st.columns(3)
        with col1:
            prob_local = st.slider("Prob. Local (%)", 0, 100, 40, key="prob_l_reg")
        with col2:
            prob_empate = st.slider("Prob. Empate (%)", 0, 100, 30, key="prob_e_reg")
        with col3:
            prob_visitante = st.slider("Prob. Visitante (%)", 0, 100, 30, key="prob_v_reg")
        
        # Factores contextuales
        col1, col2 = st.columns(2)
        with col1:
            es_final = st.checkbox("Es Final/Derby", key="final_reg")
            forma_diferencia = st.slider("Diferencia de forma", -3, 3, 0, key="forma_reg")
        with col2:
            lesiones_impact = st.slider("Impacto lesiones", -2, 2, 0, key="lesiones_reg")
            
        if submitted and equipo_local and equipo_visitante:
            # Normalizar probabilidades
            total_prob = prob_local + prob_empate + prob_visitante
            if total_prob > 0:
                prob_local_norm = prob_local / total_prob
                prob_empate_norm = prob_empate / total_prob
                prob_visitante_norm = prob_visitante / total_prob
                
                partido = {
                    'local': equipo_local,
                    'visitante': equipo_visitante,
                    'prob_local': prob_local_norm,
                    'prob_empate': prob_empate_norm,
                    'prob_visitante': prob_visitante_norm,
                    'es_final': es_final,
                    'forma_diferencia': forma_diferencia,
                    'lesiones_impact': lesiones_impact
                }
                
                if len(partidos_list) < 14:
                    partidos_list.append(partido)
                    st.success(f"Partido agregado: {equipo_local} vs {equipo_visitante}")
                    st.rerun()
                else:
                    st.error("Ya tienes 14 partidos regulares.")
    
    # Mostrar partidos existentes
    if partidos_list:
        st.subheader(f"Partidos ingresados ({len(partidos_list)}/14)")
        
        for i, partido in enumerate(partidos_list):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.text(f"{partido['local']} vs {partido['visitante']}")
            with col2:
                st.text(f"L:{partido['prob_local']:.2f} E:{partido['prob_empate']:.2f} V:{partido['prob_visitante']:.2f}")
            with col3:
                flags = []
                if partido['es_final']: flags.append("Final")
                if partido['forma_diferencia'] != 0: flags.append(f"Forma:{partido['forma_diferencia']:+d}")
                if partido['lesiones_impact'] != 0: flags.append(f"Lesiones:{partido['lesiones_impact']:+d}")
                st.text(", ".join(flags) if flags else "Normal")
            with col4:
                if st.button("🗑️", key=f"del_reg_{i}"):
                    partidos_list.pop(i)
                    st.rerun()

def entrada_partidos_revancha(partidos_list):
    """Interfaz para ingresar partidos de revancha"""
    
    with st.form("agregar_partido_revancha"):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            equipo_local = st.text_input("Equipo Local", key="local_rev")
        with col2:
            equipo_visitante = st.text_input("Equipo Visitante", key="visit_rev")
        with col3:
            submitted = st.form_submit_button("Agregar")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            prob_local = st.slider("Prob. Local (%)", 0, 100, 40, key="prob_l_rev")
        with col2:
            prob_empate = st.slider("Prob. Empate (%)", 0, 100, 30, key="prob_e_rev")
        with col3:
            prob_visitante = st.slider("Prob. Visitante (%)", 0, 100, 30, key="prob_v_rev")
            
        if submitted and equipo_local and equipo_visitante:
            total_prob = prob_local + prob_empate + prob_visitante
            if total_prob > 0:
                prob_local_norm = prob_local / total_prob
                prob_empate_norm = prob_empate / total_prob
                prob_visitante_norm = prob_visitante / total_prob
                
                partido = {
                    'local': equipo_local,
                    'visitante': equipo_visitante,
                    'prob_local': prob_local_norm,
                    'prob_empate': prob_empate_norm,
                    'prob_visitante': prob_visitante_norm
                }
                
                if len(partidos_list) < 7:
                    partidos_list.append(partido)
                    st.success(f"Partido agregado: {equipo_local} vs {equipo_visitante}")
                    st.rerun()
                else:
                    st.error("Ya tienes 7 partidos de revancha.")
    
    # Mostrar partidos de revancha
    if partidos_list:
        st.subheader(f"Partidos revancha ({len(partidos_list)}/7)")
        
        for i, partido in enumerate(partidos_list):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.text(f"{partido['local']} vs {partido['visitante']}")
            with col2:
                st.text(f"L:{partido['prob_local']:.2f} E:{partido['prob_empate']:.2f} V:{partido['prob_visitante']:.2f}")
            with col3:
                if st.button("🗑️", key=f"del_rev_{i}"):
                    partidos_list.pop(i)
                    st.rerun()

def generar_quinielas_core():
    """Genera las 4 quinielas core"""
    try:
        classifier = MatchClassifier()
        generator = PortfolioGenerator()
        
        # Clasificar partidos
        partidos_clasificados = classifier.classify_matches(st.session_state.partidos_regular)
        
        # Generar quinielas core
        quinielas_core = generator.generate_core_quinielas(partidos_clasificados)
        
        st.session_state.partidos_clasificados = partidos_clasificados
        st.session_state.quinielas_core = quinielas_core
        
        st.success("✅ Quinielas Core generadas exitosamente")
        
        # Mostrar preview
        with st.expander("Ver Quinielas Core"):
            mostrar_quinielas_preview(quinielas_core, "Core")
            
    except Exception as e:
        st.error(f"Error generando quinielas core: {str(e)}")

def generar_quinielas_satelites():
    """Genera quinielas satélites con correlación negativa"""
    if 'quinielas_core' not in st.session_state:
        st.error("Primero debes generar las quinielas Core")
        return
    
    try:
        generator = PortfolioGenerator()
        config = st.session_state.get('config', {})
        
        num_total = config.get('num_quinielas', Config.INTERFAZ['num_quinielas_default'])
        num_satelites = num_total - 4  # Restar las 4 Core
        
        quinielas_satelites = generator.generate_satellite_quinielas(
            st.session_state.partidos_clasificados,
            st.session_state.quinielas_core,
            num_satelites
        )
        
        st.session_state.quinielas_satelites = quinielas_satelites
        
        st.success(f"✅ {len(quinielas_satelites)} quinielas satélites generadas")
        
        with st.expander("Ver Quinielas Satélites"):
            mostrar_quinielas_preview(quinielas_satelites, "Satélites")
            
    except Exception as e:
        st.error(f"Error generando satélites: {str(e)}")

def ejecutar_optimizacion_grasp():
    """Ejecuta la optimización GRASP-Annealing"""
    if 'quinielas_core' not in st.session_state or 'quinielas_satelites' not in st.session_state:
        st.error("Necesitas generar Core y Satélites primero")
        return
    
    try:
        generator = PortfolioGenerator()
        validator = PortfolioValidator()
        
        # Combinar todas las quinielas
        todas_quinielas = st.session_state.quinielas_core + st.session_state.quinielas_satelites
        
        # Optimizar
        with st.spinner("🔄 Ejecutando optimización GRASP..."):
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
            for warning in validacion['warnings']:
                st.warning(warning)
                
    except Exception as e:
        st.error(f"Error en optimización: {str(e)}")

def mostrar_quinielas_preview(quinielas, titulo):
    """Muestra preview de quinielas en formato tabla"""
    if not quinielas:
        return
    
    # Crear DataFrame para mostrar
    data = []
    for i, quiniela in enumerate(quinielas[:5]):  # Solo primeras 5
        row = {'Quiniela': f'{titulo}-{i+1}'}
        for j, resultado in enumerate(quiniela['resultados']):
            row[f'P{j+1}'] = resultado
        row['Empates'] = quiniela['resultados'].count('E')
        data.append(row)
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

def mostrar_resultados():
    """Muestra análisis detallado de resultados"""
    if 'quinielas_final' not in st.session_state:
        st.info("Genera las quinielas primero")
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
            st.metric("Validación", "✅ Válido", delta="Aprobado")
        else:
            st.metric("Validación", "⚠️ Advertencias", delta="Revisar")
    
    # Distribución de resultados
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribución por Resultado")
        total_predicciones = len(quinielas) * len(st.session_state.partidos_regular)
        
        conteos = {'L': 0, 'E': 0, 'V': 0}
        for quiniela in quinielas:
            for resultado in quiniela['resultados']:
                conteos[resultado] += 1
        
        porcentajes = {k: v/total_predicciones for k, v in conteos.items()}
        
        col_l, col_e, col_v = st.columns(3)
        with col_l:
            target_l = Config.DISTRIBUCION_HISTORICA['L']
            delta_l = porcentajes['L'] - target_l
            st.metric("Locales", f"{porcentajes['L']:.1%}", delta=f"{delta_l:+.1%}")
        with col_e:
            target_e = Config.DISTRIBUCION_HISTORICA['E']
            delta_e = porcentajes['E'] - target_e
            st.metric("Empates", f"{porcentajes['E']:.1%}", delta=f"{delta_e:+.1%}")
        with col_v:
            target_v = Config.DISTRIBUCION_HISTORICA['V']
            delta_v = porcentajes['V'] - target_v
            st.metric("Visitantes", f"{porcentajes['V']:.1%}", delta=f"{delta_v:+.1%}")
        
        # Mostrar si está dentro de rangos válidos
        st.caption("Delta vs. distribución histórica objetivo")
        
        # Indicadores de rango válido
        for resultado, porcentaje in porcentajes.items():
            min_val, max_val = Config.RANGOS_HISTORICOS[resultado]
            if min_val <= porcentaje <= max_val:
                st.success(f"✅ {resultado}: {porcentaje:.1%} está en rango válido ({min_val:.1%}-{max_val:.1%})")
            else:
                st.warning(f"⚠️ {resultado}: {porcentaje:.1%} fuera de rango ({min_val:.1%}-{max_val:.1%})")
    
    with col2:
        st.subheader("Distribución de Empates")
        empates_por_quiniela = [q['resultados'].count('E') for q in quinielas]
        
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(empates_por_quiniela, bins=range(2, 8), alpha=0.7, color='steelblue')
        ax.axvline(Config.EMPATES_PROMEDIO_HISTORICO, color='red', linestyle='--', 
                  label=f'Histórico ({Config.EMPATES_PROMEDIO_HISTORICO})')
        ax.axvline(np.mean(empates_por_quiniela), color='green', linestyle='-', 
                  label=f'Actual ({np.mean(empates_por_quiniela):.2f})')
        ax.set_xlabel('Empates por Quiniela')
        ax.set_ylabel('Frecuencia')
        ax.legend()
        ax.set_title('Distribución de Empates por Quiniela')
        st.pyplot(fig)
        
        # Mostrar estadísticas de empates
        st.caption(f"Rango recomendado: {Config.EMPATES_MIN}-{Config.EMPATES_MAX} empates por quiniela")
        
        empates_fuera_rango = sum(1 for e in empates_por_quiniela 
                                if e < Config.EMPATES_MIN or e > Config.EMPATES_MAX)
        if empates_fuera_rango > 0:
            st.warning(f"⚠️ {empates_fuera_rango} quinielas fuera del rango recomendado")
        else:
            st.success("✅ Todas las quinielas en rango de empates válido")
    
    # Tabla completa de quinielas
    st.subheader("Todas las Quinielas")
    mostrar_tabla_completa(quinielas)

def mostrar_tabla_completa(quinielas):
    """Muestra tabla completa con todas las quinielas"""
    if not quinielas or not st.session_state.partidos_regular:
        return
    
    # Crear DataFrame
    data = []
    partidos = st.session_state.partidos_regular
    
    for i, quiniela in enumerate(quinielas):
        row = {'Q': f'Q-{i+1}'}
        
        # Agregar resultados por partido
        for j, resultado in enumerate(quiniela['resultados']):
            if j < len(partidos):
                partido_nombre = f"{partidos[j]['local'][:8]} vs {partidos[j]['visitante'][:8]}"
                row[f'P{j+1}'] = resultado
            else:
                row[f'P{j+1}'] = resultado
        
        # Estadísticas
        row['Empates'] = quiniela['resultados'].count('E')
        row['Prob≥11'] = f"{quiniela.get('prob_11_plus', 0):.1%}"
        
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Colorear celdas según resultado
    def highlight_resultado(val):
        if val == 'L':
            return 'background-color: lightblue'
        elif val == 'E':
            return 'background-color: lightgray'
        elif val == 'V':
            return 'background-color: lightcoral'
        return ''
    
    # Aplicar estilo solo a columnas de partidos
    partido_cols = [col for col in df.columns if col.startswith('P')]
    
    styled_df = df.style.applymap(highlight_resultado, subset=partido_cols)
    
    st.dataframe(styled_df, use_container_width=True)

def exportar_resultados():
    """Exporta resultados en múltiples formatos"""
    quinielas = st.session_state.quinielas_final
    partidos = st.session_state.partidos_regular
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Exportar CSV
        csv_buffer = io.StringIO()
        df = crear_dataframe_export(quinielas, partidos)
        df.to_csv(csv_buffer, index=False)
        
        st.download_button(
            label="📁 Descargar CSV",
            data=csv_buffer.getvalue(),
            file_name=f"progol_quinielas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Exportar JSON
        json_data = {
            'fecha_generacion': datetime.now().isoformat(),
            'partidos': partidos,
            'quinielas': quinielas,
            'estadisticas': calcular_estadisticas_export(quinielas)
        }
        
        st.download_button(
            label="📄 Descargar JSON",
            data=json.dumps(json_data, indent=2, ensure_ascii=False),
            file_name=f"progol_quinielas_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )
    
    with col3:
        # Exportar formato Progol
        progol_format = generar_formato_progol(quinielas)
        
        st.download_button(
            label="🎯 Formato Progol",
            data=progol_format,
            file_name=f"progol_boletos_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain"
        )

def crear_dataframe_export(quinielas, partidos):
    """Crea DataFrame para exportación"""
    data = []
    
    for i, quiniela in enumerate(quinielas):
        row = {'Quiniela': f'Q-{i+1}'}
        
        for j, resultado in enumerate(quiniela['resultados']):
            if j < len(partidos):
                partido = partidos[j]
                row[f'Partido_{j+1}'] = f"{partido['local']} vs {partido['visitante']}"
                row[f'Resultado_{j+1}'] = resultado
            else:
                row[f'Resultado_{j+1}'] = resultado
        
        row['Total_Empates'] = quiniela['resultados'].count('E')
        row['Prob_11_Plus'] = quiniela.get('prob_11_plus', 0)
        
        data.append(row)
    
    return pd.DataFrame(data)

def calcular_estadisticas_export(quinielas):
    """Calcula estadísticas para exportación"""
    total_predicciones = len(quinielas) * 14
    conteos = {'L': 0, 'E': 0, 'V': 0}
    
    for quiniela in quinielas:
        for resultado in quiniela['resultados']:
            conteos[resultado] += 1
    
    return {
        'total_quinielas': len(quinielas),
        'distribucion': {k: v/total_predicciones for k, v in conteos.items()},
        'empates_promedio': np.mean([q['resultados'].count('E') for q in quinielas]),
        'prob_11_plus_promedio': np.mean([q.get('prob_11_plus', 0) for q in quinielas])
    }

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
    
    output.append("")
    output.append("ESTADÍSTICAS:")
    
    # Calcular estadísticas
    empates_por_quiniela = [q['resultados'].count('E') for q in quinielas]
    output.append(f"Empates promedio: {np.mean(empates_por_quiniela):.2f}")
    output.append(f"Rango empates: {min(empates_por_quiniela)} - {max(empates_por_quiniela)}")
    
    return "\n".join(output)

if __name__ == "__main__":
    main()