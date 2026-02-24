import flag


def get_clean_flag(country_name):
    # F1 countries often use shorthand, so we map them to ISO-2 codes first
    mapping = {
        "UK": "GB", "USA": "US", "UAE": "AE", "Netherlands": "NL", 
        "Saudi Arabia": "SA", "Italy": "IT", "Japan": "JP"
    }
    iso_code = mapping.get(country_name, country_name[:2].upper())
    
    try:
        # This library ensures the characters are paired correctly for modern UIs
        return flag.flag(iso_code) 
    except:
        return "🏁" # Fallback if code is invalid


