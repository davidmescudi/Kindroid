"""
Basic example of using the Kindroid robot.
"""
import time
from kindroid.robot import Robot


def handle_qr_code(data: str, code_type: str):
    """Callback function for QR code detection."""
    print(f"\nQR Code detected!")
    print(f"Data: {data}")
    print(f"Type: {code_type}")


def handle_llm_response(response: str):
    """Callback function for LLM responses."""
    print(f"\nRobot: {response}")


def main():
    # Initialize the robot
    robot = Robot()
    
    # Register QR code callback before initialization
    robot.register_qr_callback(handle_qr_code)
    
    if not robot.initialize():
        print("Failed to initialize robot")
        return
    
    print("Robot initialized successfully")
    print("Status:", robot.get_status())
    print("\nQR code detection is running in the background...")
    
    # Display available LLM models
    available_models = robot.llm.list_available_models()
    print("\nAvailable LLM models:")
    for i, model in enumerate(available_models, 1):
        print(f"{i}. {model}")
    
    try:
        while True:
            print("\nOptions:")
            # TODO: Should the robot be able to handle a conversation with a human or should it be a one-way conversation?
            # e.g. Are we continously listening for speech or only when the user speaks? Are we interrupting the user when they are speaking or are we stoping the llm when the user is speaking?
            print("1. Start continuous interaction (speech -> LLM -> speech)")
            print("2. Single interaction (speech -> LLM -> speech)")
            print("3. Update LLM settings")
            print("4. Update audio settings")
            print("5. Update speech recognition settings")
            print("6. Change LLM model")
            print("7. Exit")
            
            choice = input("Enter your choice (1-7): ")
            
            if choice == "1":
                print("Starting continuous interaction... (Press Ctrl+C to stop)")
                robot.start_interaction(handle_llm_response)
                
                # Keep the main thread alive while interaction is running
                try:
                    while robot.is_interacting:
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    robot.stop_interaction()
                    print("\nStopped interaction")
            
            elif choice == "2":
                print("Starting single interaction...")
                response = robot.process_interaction()
                if response:
                    print(f"Robot: {response}")
                else:
                    print("No response generated")
            
            elif choice == "3":
                print("Update LLM settings:")
                temperature = float(input("Enter temperature (0.0-1.0): "))
                max_tokens = int(input("Enter max tokens: "))
                system_prompt = input("Enter system prompt: ")
                
                robot.update_llm_settings(
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt
                )
                print("Settings updated")
            
            elif choice == "4":
                print("Update audio settings:")
                rate = int(input("Enter speech rate (default 150): ") or "150")
                volume = float(input("Enter volume (0.0-1.0): ") or "1.0")
                
                robot.update_audio_settings(rate=rate, volume=volume)
                print("Settings updated")
            
            elif choice == "5":
                print("Update speech recognition settings:")
                energy = int(input("Enter energy threshold (default 300): ") or "300")
                pause = float(input("Enter pause threshold in seconds (default 0.8): ") or "0.8")
                phrase = float(input("Enter phrase threshold in seconds (default 0.3): ") or "0.3")
                non_speaking = float(input("Enter non-speaking duration in seconds (default 0.5): ") or "0.5")
                
                robot.update_recognition_settings(
                    energy_threshold=energy,
                    pause_threshold=pause,
                    phrase_threshold=phrase,
                    non_speaking_duration=non_speaking
                )
                print("Settings updated")
            
            elif choice == "6":
                available_models = robot.llm.list_available_models()
                if not available_models:
                    print("No models available")
                    continue
                
                print("\nAvailable models:")
                for i, model in enumerate(available_models, 1):
                    print(f"{i}. {model}")
                
                try:
                    model_idx = int(input("\nSelect model number: ")) - 1
                    if 0 <= model_idx < len(available_models):
                        robot.update_llm_settings(model=available_models[model_idx])
                        print(f"Switched to model: {available_models[model_idx]}")
                    else:
                        print("Invalid model number")
                except ValueError:
                    print("Invalid input")
            
            elif choice == "7":
                break
            
            else:
                print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nStopping robot...")
    finally:
        robot.shutdown()
        print("Robot shut down")


if __name__ == "__main__":
    main() 