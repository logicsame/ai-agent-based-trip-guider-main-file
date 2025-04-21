import os
import secrets
import string

def generate_simple_key(length=64):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    # Generate a secure secret key
    secret_key = generate_simple_key(64)
    
    print("\n=== JWT Secret Key Generator ===\n")
    print(f"Your generated SECRET_KEY is:\n\n{secret_key}\n")
    print("Copy this key and use it in your .env file for the SECRET_KEY variable.")
    print("IMPORTANT: Keep this key secret and don't share it publicly!")
    
    # Ask if user wants to update the .env file directly
    update_env = input("\nDo you want to update your .env file with this key? (y/n): ")
    
    if update_env.lower() == 'y':
        env_path = os.path.join(os.getcwd(), '.env')
        
        if os.path.exists(env_path):
            # Read the current .env file
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update the SECRET_KEY line
            with open(env_path, 'w') as f:
                for line in lines:
                    if line.startswith('SECRET_KEY='):
                        f.write(f'SECRET_KEY={secret_key}\n')
                    else:
                        f.write(line)
            
            print(f"\nUpdated SECRET_KEY in {env_path}")
        else:
            print(f"\nError: .env file not found at {env_path}")
            print("Please create the .env file first or run the setup.sh script.")
