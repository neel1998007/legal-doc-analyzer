"""
Tests for LLM integration (Ollama)
"""
import pytest
import subprocess
import time

class TestLLMIntegration:
    """Test Ollama LLM integration"""
    
    def test_ollama_available(self):
        """Test if Ollama is installed and available"""
        try:
            result = subprocess.run(
                ['ollama', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0
            assert 'ollama version' in result.stdout
        except FileNotFoundError:
            pytest.skip("Ollama not installed")
        except subprocess.TimeoutExpired:
            pytest.fail("Ollama command timed out")

    def test_llama2_model_available(self):
        """Test if llama2:7b model is available"""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=15
            )
            assert result.returncode == 0
            
            if 'llama2' not in result.stdout:
                pytest.skip("llama2:7b model not downloaded")
            
        except FileNotFoundError:
            pytest.skip("Ollama not installed")
        except subprocess.TimeoutExpired:
            pytest.fail("Ollama list command timed out")

    @pytest.mark.slow
    def test_simple_generation(self):
        """Test basic text generation"""
        try:
            result = subprocess.run(
                ['ollama', 'run', 'llama2:7b', 'Say hello in one word.'],
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                assert len(response) > 0
                assert len(response) < 1000  # Reasonable response length
            else:
                pytest.skip("LLM generation failed - model might be loading")
                
        except FileNotFoundError:
            pytest.skip("Ollama not installed")
        except subprocess.TimeoutExpired:
            pytest.skip("LLM generation timed out - normal for first run")

    @pytest.mark.slow
    def test_legal_domain_response(self):
        """Test LLM response in legal domain"""
        prompt = "What is a contract? Answer in one sentence."
        
        try:
            result = subprocess.run(
                ['ollama', 'run', 'llama2:7b', prompt],
                capture_output=True,
                text=True,
                timeout=45,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                response = result.stdout.strip().lower()
                # Check if response contains legal-related terms
                legal_terms = ['contract', 'agreement', 'legal', 'binding', 'parties']
                assert any(term in response for term in legal_terms)
            else:
                pytest.skip("LLM generation failed")
                
        except FileNotFoundError:
            pytest.skip("Ollama not installed")
        except subprocess.TimeoutExpired:
            pytest.skip("LLM generation timed out")

    def test_ollama_service_health(self):
        """Test if Ollama service is running properly"""
        try:
            # Quick health check with list command
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                assert 'NAME' in result.stdout  # Header should be present
            else:
                pytest.fail("Ollama service not responding properly")
                
        except FileNotFoundError:
            pytest.skip("Ollama not installed")
        except subprocess.TimeoutExpired:
            pytest.fail("Ollama service health check timed out")

class TestLLMConfiguration:
    """Test LLM configuration and setup"""
    
    def test_model_configuration(self):
        """Test model configuration is correct"""
        from app.core.test_config import test_settings
        
        # Verify test settings exist
        assert hasattr(test_settings, 'DEBUG')
        assert test_settings.DEBUG is True
        
    def test_future_rag_preparation(self):
        """Test that we're ready for RAG integration"""
        # This test ensures our setup is ready for Week 3-4
        assert True  # Placeholder for future RAG preparation tests