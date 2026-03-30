"""
Analysis Service - Manages analysis sessions, slides, and visualizations.
Follows Single Responsibility Principle - only handles analysis management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os
import time

import streamlit as st

from domain.entities import (
    Analysis,
    Slide,
    Visualization,
    VisualizationConfig,
    UserSession,
)

from domain.value_objects import VisualizationType


class AnalysisRepository:
    """Repository interface for analysis persistence."""

    def save(self, analysis: Analysis) -> bool:
        raise NotImplementedError

    def load(self, analysis_id: str) -> Optional[Analysis]:
        raise NotImplementedError

    def delete(self, analysis_id: str) -> bool:
        raise NotImplementedError

    def list_all(self) -> List[Analysis]:
        raise NotImplementedError


class FileAnalysisRepository(AnalysisRepository):
    """File-based implementation of AnalysisRepository."""

    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def save(self, analysis: Analysis) -> bool:
        try:
            file_path = os.path.join(self.storage_dir, f"{analysis.id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(analysis.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return False

    def load(self, analysis_id: str) -> Optional[Analysis]:
        try:
            file_path = os.path.join(self.storage_dir, f"{analysis_id}.json")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return Analysis.from_dict(data)
        except Exception as e:
            print(f"Error loading analysis: {e}")
        return None

    def delete(self, analysis_id: str) -> bool:
        try:
            file_path = os.path.join(self.storage_dir, f"{analysis_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting analysis: {e}")
            return False

    def list_all(self) -> List[Analysis]:
        analyses = []
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    analysis_id = filename[:-5]
                    analysis = self.load(analysis_id)
                    if analysis:
                        analyses.append(analysis)
        except Exception as e:
            print(f"Error listing analyses: {e}")
        return analyses


class AnalysisService:
    """
    Service for managing analyses, slides, and visualizations.
    With proper loading feedback and missing methods added.
    """

    def __init__(self, repository: Optional[AnalysisRepository] = None):
        self.repository = repository or FileAnalysisRepository()
        self._session: Optional[UserSession] = None

    # ====================== SESSION ======================
    def initialize_session(self, session_data: Optional[Dict[str, Any]] = None) -> UserSession:
        if session_data:
            self._session = UserSession.from_dict(session_data)
        else:
            self._session = UserSession()
        return self._session

    def get_session(self) -> UserSession:
        if self._session is None:
            self._session = UserSession()
        return self._session

    # ====================== ANALYSIS MANAGEMENT ======================
    def create_analysis(self, name: str = "Nova Análise") -> Analysis:
        try:
            with st.spinner("Criando nova análise..."):
                time.sleep(0.4)
                session = self.get_session()
                analysis = session.create_analysis(name)
                self.repository.save(analysis)

            st.success(f"✅ Análise **'{name}'** criada com sucesso!", icon="🎉")
            st.toast("Análise criada com sucesso!", icon="✅")
            return analysis

        except Exception as e:
            st.error(f"❌ Erro ao criar análise: {str(e)}", icon="🚨")
            st.toast("Falha ao criar análise", icon="❌")
            raise

    def save_current_analysis(self) -> bool:
        try:
            progress_bar = st.progress(0, text="Salvando análise...")
            
            for percent in range(0, 101, 20):
                time.sleep(0.08)
                progress_bar.progress(percent, text=f"Salvando... {percent}%")

            analysis = self.get_current_analysis()
            if not analysis:
                st.warning("Nenhuma análise ativa para salvar.")
                return False

            success = self.repository.save(analysis)
            
            if success:
                progress_bar.progress(100, text="✅ Salvo com sucesso!")
                st.success("💾 Análise salva com sucesso!", icon="💾")
                st.toast("Análise salva", icon="💾")
                return True
            else:
                st.error("❌ Falha ao salvar a análise.")
                return False

        except Exception as e:
            st.error(f"❌ Erro ao salvar análise: {str(e)}", icon="🚨")
            return False
        finally:
            time.sleep(0.3)

    def get_current_analysis(self) -> Optional[Analysis]:
        session = self.get_session()
        return session.get_current_analysis()

    # ====================== SLIDE MANAGEMENT ======================
    def get_current_slide(self) -> Optional[Slide]:
        """Get the currently active slide - MÉTODO QUE ESTAVA FALTANDO"""
        analysis = self.get_current_analysis()
        if not analysis or not analysis.slides:
            return None
        
        session = self.get_session()
        current_slide_id = getattr(session, 'current_slide_id', None)
        
        if current_slide_id:
            for slide in analysis.slides:
                if getattr(slide, 'id', None) == current_slide_id:
                    return slide
        
        # Fallback: retorna o primeiro slide
        return analysis.slides[0] if analysis.slides else None

    def add_slide(self, title: Optional[str] = None) -> Optional[Slide]:
        analysis = self.get_current_analysis()
        if analysis:
            slide = Slide(title=title or f"Slide {len(analysis.slides) + 1}")
            analysis.add_slide(slide)
            
            # Atualiza o slide atual
            session = self.get_session()
            session.current_slide_id = slide.id
            
            self.repository.save(analysis)
            return slide
        return None

    def set_current_slide(self, slide_id: str) -> Optional[Slide]:
        """Set the current active slide."""
        analysis = self.get_current_analysis()
        if analysis:
            for slide in analysis.slides:
                if getattr(slide, 'id', None) == slide_id:
                    session = self.get_session()
                    session.current_slide_id = slide_id
                    self.repository.save(analysis)
                    return slide
        return None

    def delete_slide(self, slide_id: str) -> bool:
        analysis = self.get_current_analysis()
        if analysis and len(analysis.slides) > 1:
            # Remove o slide
            analysis.slides = [s for s in analysis.slides if getattr(s, 'id', None) != slide_id]
            
            # Atualiza slide atual se necessário
            session = self.get_session()
            if getattr(session, 'current_slide_id', None) == slide_id:
                session.current_slide_id = analysis.slides[0].id if analysis.slides else None
            
            self.repository.save(analysis)
            return True
        return False

    # ====================== VISUALIZATION MANAGEMENT ======================
    def delete_visualization(self, slide_id: str, viz_id: str) -> bool:
        analysis = self.get_current_analysis()
        if analysis:
            for slide in analysis.slides:
                if getattr(slide, 'id', None) == slide_id:
                    if hasattr(slide, 'remove_visualization'):
                        result = slide.remove_visualization(viz_id)
                        if result:
                            self.repository.save(analysis)
                        return result
        return False

    # ====================== OUTROS MÉTODOS ======================
    def get_analysis_history(self) -> List[Dict[str, Any]]:
        session = self.get_session()
        return [
            {
                "id": a.id,
                "name": a.name,
                "created_at": getattr(a, 'created_at', datetime.now()).isoformat(),
                "updated_at": getattr(a, 'updated_at', datetime.now()).isoformat(),
                "slide_count": len(getattr(a, 'slides', [])),
                "file_name": getattr(getattr(a, 'data_schema', None), 'file_name', None),
            }
            for a in getattr(session, 'analyses', [])
        ]

    def save_session(self) -> Dict[str, Any]:
        if self._session:
            return self._session.to_dict()
        return {}

    def load_saved_analyses(self) -> List[Analysis]:
        try:
            with st.spinner("Carregando histórico de análises..."):
                time.sleep(0.5)
                analyses = self.repository.list_all()
            
            if analyses:
                st.success(f"✅ {len(analyses)} análises carregadas", icon="📋")
            return analyses
        except Exception as e:
            st.error(f"❌ Erro ao carregar análises: {str(e)}", icon="🚨")
            return []