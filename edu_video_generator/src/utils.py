import os
import logging
import shutil

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_dir_exists(dir_path: str):
    """Creates a directory if it doesn't exist."""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            logger.info(f"Created directory: {dir_path}")
        except OSError as e:
            logger.error(f"Error creating directory {dir_path}: {e}")
            raise # Re-raise the exception after logging

def cleanup_dir(dir_path: str):
    """Removes all files and subdirectories within a given directory."""
    if not os.path.isdir(dir_path):
        logger.warning(f"Cleanup requested for non-existent or non-directory path: {dir_path}")
        return
    try:
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f'Failed to delete {file_path}. Reason: {e}')
        logger.info(f"Cleaned up directory: {dir_path}")
    except Exception as e:
        logger.error(f"Error during cleanup of directory {dir_path}: {e}")

# Example usage (optional, can be removed)
if __name__ == '__main__':
    test_dir = 'temp_test_dir'
    ensure_dir_exists(test_dir)
    # Create a dummy file
    with open(os.path.join(test_dir, 'dummy.txt'), 'w') as f:
        f.write('test')
    print(f"Directory '{test_dir}' exists: {os.path.exists(test_dir)}")
    cleanup_dir(test_dir)
    print(f"Directory '{test_dir}' exists after cleanup: {os.path.exists(test_dir)}") # Should be True, but empty
    os.rmdir(test_dir) # Remove the directory itself
    print(f"Directory '{test_dir}' removed.")
