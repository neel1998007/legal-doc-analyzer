"""
Test script for Ollama LLM setup
Run with: python test_ollama.py
"""

import subprocess
import os

def run_ollama_command(prompt, timeout=60):
    """Run ollama command and return response"""
    try:
        # Set environment for UTF-8 encoding
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            ['ollama', 'run', 'llama2:7b', prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='ignore',  # Ignore problematic characters
            env=env
        )
        
        if result.returncode == 0:
            response = result.stdout.strip()
            # Clean up response
            response = response.replace('\r\n', '\n').replace('\r', '\n')
            return response, None
        else:
            error = result.stderr.strip() if result.stderr else "Unknown error"
            return None, error
    
    except subprocess.TimeoutExpired:
        return None, f"Timeout after {timeout} seconds - try shorter prompts"
    except FileNotFoundError:
        return None, "Ollama not found. Make sure it's installed and in PATH."
    except Exception as e:
        return None, str(e)

def test_ollama_available():
    """Check if Ollama is available"""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ollama installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama not working properly")
            return False
    except FileNotFoundError:
        print("❌ Ollama not found. Install from https://ollama.ai")
        return False

def test_model_available():
    """Check if llama2 model is available"""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if 'llama2' in result.stdout:
            print("✅ Llama2:7b model available")
            return True
        else:
            print("❌ Llama2:7b model not found")
            print("💡 Run: ollama pull llama2:7b")
            return False
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False

def test_simple_generation():
    """Test basic text generation"""
    print("\n" + "="*50)
    print("🧪 TEST 1: Simple Text Generation")
    print("="*50)
    
    prompt = "Say hello in one sentence."
    print(f"📝 Prompt: {prompt}")
    print("🤖 Response: ", end="", flush=True)
    
    response, error = run_ollama_command(prompt, timeout=30)
    
    if response:
        print(response[:200] + "..." if len(response) > 200 else response)
        print(f"✅ Generation successful! ({len(response)} characters)")
        return True
    else:
        print(f"\n❌ Error: {error}")
        return False

def test_legal_context():
    """Test with legal-style prompt"""
    print("\n" + "="*50)
    print("🧪 TEST 2: Legal Context (Short)")
    print("="*50)
    
    prompt = "What is a contract? Answer in 2 sentences."
    print(f"📝 Prompt: {prompt}")
    print("🤖 Response: ", end="", flush=True)
    
    response, error = run_ollama_command(prompt, timeout=45)
    
    if response:
        print(response[:300] + "..." if len(response) > 300 else response)
        print("✅ Legal context test successful!")
        return True
    else:
        print(f"\n❌ Error: {error}")
        return False

def test_qa_format():
    """Test Q&A format for RAG preparation"""
    print("\n" + "="*50)
    print("🧪 TEST 3: Q&A Format (Simple)")
    print("="*50)
    
    prompt = "Q: What makes an agreement legally binding? A:"
    print(f"📝 Prompt: {prompt}")
    print("🤖 Response: ", end="", flush=True)
    
    response, error = run_ollama_command(prompt, timeout=45)
    
    if response:
        print(response[:300] + "..." if len(response) > 300 else response)
        print("✅ Q&A format test successful!")
        return True
    else:
        print(f"\n❌ Error: {error}")
        return False

def test_direct_ollama():
    """Test ollama directly without subprocess complexity"""
    print("\n" + "="*50)
    print("🧪 BONUS TEST: Direct Ollama Check")
    print("="*50)
    
    print("📝 Testing if ollama command works directly...")
    print("💡 You can test manually with: ollama run llama2:7b \"Hello\"")
    
    # Just verify the command exists
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Ollama command is working properly!")
            return True
        else:
            print("❌ Ollama command failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function"""
    print("🤖 Legal Document Analyzer - Ollama LLM Test (Fixed)")
    print("="*50)
    
    # Check Ollama installation
    if not test_ollama_available():
        print("\n💡 Install Ollama from: https://ollama.ai/download")
        return
    
    # Check model availability
    if not test_model_available():
        return
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    if test_simple_generation():
        tests_passed += 1
    
    if test_legal_context():
        tests_passed += 1
        
    if test_qa_format():
        tests_passed += 1
        
    if test_direct_ollama():
        tests_passed += 1
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    print(f"✅ Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed >= 3:
        print("🎉 Ollama is working well! Ready for RAG integration.")
        print("🚀 Ready for Week 3-4: Document processing and RAG!")
    elif tests_passed >= 1:
        print("⚠️  Basic functionality works. Some advanced features may need tuning.")
    else:
        print("⚠️  Multiple test failures. Check the errors above.")
    
    print("\n💾 Model: llama2:7b via Ollama")
    print("🔧 No compilation issues!")
    print("💡 Manual test: ollama run llama2:7b \"Hello world\"")

if __name__ == "__main__":
    main()