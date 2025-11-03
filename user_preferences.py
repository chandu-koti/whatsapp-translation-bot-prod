# user_preferences.py
import json
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class UserPreferences:
    """Manages user language preferences"""
    
    def __init__(self, storage_file: str = 'user_prefs.json'):
        self.storage_file = storage_file
        self.preferences = self._load_preferences()
        # Temporary selection basket (for multi-select)
        self.temp_selections = {}
        logger.info(f"✅ UserPreferences initialized with {len(self.preferences)} users")
    
    def _load_preferences(self) -> Dict:
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                    logger.info(f"📂 Loaded preferences for {len(prefs)} users")
                    return prefs
            except Exception as e:
                logger.error(f"❌ Error loading preferences: {str(e)}")
                return {}
        else:
            logger.info("📂 No existing preferences file, starting fresh")
            return {}
    
    def _save_preferences(self):
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Saved preferences for {len(self.preferences)} users")
        except Exception as e:
            logger.error(f"❌ Error saving preferences: {str(e)}")
    
    def get_user_languages(self, user_id: str) -> List[str]:
        """Get saved languages for user"""
        if user_id in self.preferences:
            langs = self.preferences[user_id].get('languages', [])
            if langs:
                logger.info(f"👤 User {user_id} languages: {langs}")
                return langs
        
        # Return empty list for new users (they need to select)
        logger.info(f"👤 New user {user_id}, no languages selected yet")
        return []
    
    def set_user_languages(self, user_id: str, languages: List[str]) -> bool:
        try:
            if user_id not in self.preferences:
                self.preferences[user_id] = {}
            
            self.preferences[user_id]['languages'] = languages
            self._save_preferences()
            logger.info(f"✅ Set languages for {user_id}: {languages}")
            return True
        except Exception as e:
            logger.error(f"❌ Error setting languages: {str(e)}")
            return False
    
    # NEW: Temporary selection methods for multi-select
    def get_temp_selections(self, user_id: str) -> List[str]:
        """Get temporary selections (shopping cart)"""
        return self.temp_selections.get(user_id, [])
    
    def add_temp_selection(self, user_id: str, lang_code: str):
        """Add language to temporary selection"""
        if user_id not in self.temp_selections:
            self.temp_selections[user_id] = []
        
        if lang_code not in self.temp_selections[user_id]:
            self.temp_selections[user_id].append(lang_code)
            logger.info(f"➕ Added {lang_code} to temp for {user_id}")
    
    def clear_temp_selections(self, user_id: str):
        """Clear temporary selections"""
        if user_id in self.temp_selections:
            del self.temp_selections[user_id]
            logger.info(f"🗑️ Cleared temp selections for {user_id}")
    
    def confirm_temp_selections(self, user_id: str) -> bool:
        """Save temporary selections as permanent"""
        temp_langs = self.get_temp_selections(user_id)
        if temp_langs:
            self.set_user_languages(user_id, temp_langs)
            self.clear_temp_selections(user_id)
            return True
        return False
    
    def get_user_romaji_preference(self, user_id: str) -> bool:
        if user_id in self.preferences:
            return self.preferences[user_id].get('use_romaji', False)
        return False
    
    def set_user_romaji_preference(self, user_id: str, use_romaji: bool) -> bool:
        try:
            if user_id not in self.preferences:
                self.preferences[user_id] = {}
            
            self.preferences[user_id]['use_romaji'] = use_romaji
            self._save_preferences()
            logger.info(f"✅ Set Romaji preference for {user_id}: {use_romaji}")
            return True
        except Exception as e:
            logger.error(f"❌ Error setting Romaji preference: {str(e)}")
            return False
    
    def reset_user_preferences(self, user_id: str) -> bool:
        try:
            if user_id in self.preferences:
                del self.preferences[user_id]
                self._save_preferences()
                logger.info(f"🔄 Reset preferences for {user_id}")
            if user_id in self.temp_selections:
                del self.temp_selections[user_id]
            return True
        except Exception as e:
            logger.error(f"❌ Error resetting preferences: {str(e)}")
            return False