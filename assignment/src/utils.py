import yaml
from typing import List
from pathlib import Path


def read_config(file_path):
    """
    Reads the configuration file and returns the configuration as a dictionary.
    
    Args:
        file_path (Path): The path to the configuration file.
    
    Returns:
        dict: The configuration dictionary.
    """
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def get_user(username: str, email: str):
    """
    Retrieves the folders accessible by the user based on the username and email.
    
    Args:
        username (str): The username of the user.
        email (str): The email of the user.
    
    Returns:
        List[str]: A list of folder names accessible by the user.
    """
    config_file_path = Path(__file__).parent / 'config.yaml'
    config = read_config(config_file_path)
    users = config.get('users', {})   
    for user, user_info in users.items():
        if user.lower() == username.lower() and user_info.get('email') == email:
            return user_info.get('folders', [])    
    return "User or email not found !!!"


def find_folders(d, key="folders"):
    """
    Finds and returns a list of folder names from the configuration file where the specified key is present.
    
    Args:
        key (str): The key to search for in the configuration file. Default is "folders".
    
    Returns:
        A list of folder names.
    """
    folders = []
    if isinstance(d, dict):
        for k, v in d.items():
            if k == key:
                folders.extend(v)
            elif isinstance(v, dict):
                folders.extend(find_folders(v, key))
            elif isinstance(v, list):
                for item in v:
                    folders.extend(find_folders(item, key))
    return folders

