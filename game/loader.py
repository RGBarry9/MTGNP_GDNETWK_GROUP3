# game/loader.py
import json
import os
from typing import Dict, List, Optional, Any

from models.card import Card
from models.ability import Ability


class CardLoader:
    """
    Loads the card database from a JSON file.
    
    The card database contains all available cards that players can use
    to build their decks. Both the server and clients must use the same
    card database.
    
    Expected JSON format:
    {
        "card_id": "lightning_bolt_001",
        "name": "Lightning Bolt",
        "card_type": "Instant",
        "mana_cost": "R",
        "text": "Deal 3 damage to any target.",
        "colors": ["R"],
        "power": null,
        "toughness": null,
        "keywords": [],
        "effects": [
            {
                "effect_type": "DAMAGE",
                "amount": 3,
                "target_type": "ANY"
            }
        ],
        "trigger": null,
        "abilities": null
    }
    """

    def __init__(self):
        """Initialize the CardLoader."""
        self.cards: Dict[str, Card] = {}
        self._loaded = False

    def load(self, filename: str) -> Dict[str, Card]:
        """
        Load cards from a JSON file.
        
        Args:
            filename: Path to the cards.json file
            
        Returns:
            Dict[str, Card]: Dictionary mapping card_id to Card objects
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
            ValueError: If required fields are missing
        """
        # Check if file exists
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Card database not found: {filename}")
        
        # Load and parse JSON
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        # Validate and parse each card
        cards = {}
        for item in data:
            card = self._parse_card(item)
            cards[card.card_id] = card
        
        self.cards = cards
        self._loaded = True
        
        print(f"✅ Loaded {len(cards)} cards from {filename}")
        return cards

    def load_from_dict(self, data: List[Dict[str, Any]]) -> Dict[str, Card]:
        """
        Load cards from a dictionary (useful for testing).
        
        Args:
            data: List of card dictionaries
            
        Returns:
            Dict[str, Card]: Dictionary mapping card_id to Card objects
        """
        cards = {}
        for item in data:
            card = self._parse_card(item)
            cards[card.card_id] = card
        
        self.cards = cards
        self._loaded = True
        
        print(f"✅ Loaded {len(cards)} cards from dictionary")
        return cards

    def _parse_card(self, data: Dict[str, Any]) -> Card:
        """
        Parse a single card dictionary into a Card object.
        
        Args:
            data: Card data dictionary
            
        Returns:
            Card: Parsed Card object
            
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        required_fields = ["card_id", "name", "card_type"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field '{field}' in card: {data}")
        
        # Create card with basic fields
        card = Card(
            card_id=data["card_id"],
            name=data["name"],
            card_type=data["card_type"],
            mana_cost=data.get("mana_cost", ""),
            text=data.get("text", ""),
            colors=data.get("colors", []),
            keywords=data.get("keywords", []),
            abilities=[],  # Will be populated below
            trigger=data.get("trigger"),
            effects=data.get("effects", [])
        )
        
        # Set creature stats if present
        if "power" in data and data["power"] is not None:
            card.power = data["power"]
        if "toughness" in data and data["toughness"] is not None:
            card.toughness = data["toughness"]
        
        # Parse abilities if present
        if "abilities" in data and data["abilities"]:
            for ability_data in data["abilities"]:
                ability = self._parse_ability(ability_data)
                card.add_ability(ability)
        
        return card

    def _parse_ability(self, data: Dict[str, Any]) -> Ability:
        """
        Parse an ability dictionary into an Ability object.
        
        Args:
            data: Ability data dictionary
            
        Returns:
            Ability: Parsed Ability object
        """
        return Ability(
            name=data.get("name", "Unknown Ability"),
            ability_type=data.get("ability_type", ""),
            cost=data.get("cost", {}),
            text=data.get("text", ""),
            effect=data.get("effect", {}),
            targets=data.get("targets", 0)
        )

    # ==========================================================
    # Card Retrieval Methods
    # ==========================================================

    def get_card(self, card_id: str) -> Optional[Card]:
        """
        Get a card by its ID.
        
        Args:
            card_id: The card's unique identifier
            
        Returns:
            Optional[Card]: The card if found, None otherwise
        """
        if not self._loaded:
            raise RuntimeError("CardLoader not loaded. Call load() first.")
        return self.cards.get(card_id)

    def get_cards(self, card_ids: List[str]) -> List[Card]:
        """
        Get multiple cards by their IDs.
        
        Args:
            card_ids: List of card IDs
            
        Returns:
            List[Card]: List of found cards (missing cards are skipped)
        """
        if not self._loaded:
            raise RuntimeError("CardLoader not loaded. Call load() first.")
        
        cards = []
        for card_id in card_ids:
            card = self.cards.get(card_id)
            if card:
                cards.append(card)
        return cards

    def get_all_cards(self) -> List[Card]:
        """Get all loaded cards."""
        if not self._loaded:
            raise RuntimeError("CardLoader not loaded. Call load() first.")
        return list(self.cards.values())

    def get_cards_by_type(self, card_type: str) -> List[Card]:
        """
        Get all cards of a specific type.
        
        Args:
            card_type: The card type to filter by (e.g., "Creature", "Land")
            
        Returns:
            List[Card]: List of cards with the specified type
        """
        if not self._loaded:
            raise RuntimeError("CardLoader not loaded. Call load() first.")
        return [card for card in self.cards.values() if card.card_type == card_type]

    def get_cards_by_color(self, color: str) -> List[Card]:
        """
        Get all cards of a specific color.
        
        Args:
            color: The color to filter by (R, G, B, U, W, C)
            
        Returns:
            List[Card]: List of cards with the specified color
        """
        if not self._loaded:
            raise RuntimeError("CardLoader not loaded. Call load() first.")
        return [card for card in self.cards.values() if color in card.colors]

    def get_cards_by_name(self, name: str) -> List[Card]:
        """
        Get all cards with a specific name.
        
        Args:
            name: The card name to search for
            
        Returns:
            List[Card]: List of cards with the specified name
        """
        if not self._loaded:
            raise RuntimeError("CardLoader not loaded. Call load() first.")
        return [card for card in self.cards.values() if card.name == name]

    # ==========================================================
    # Deck Validation
    # ==========================================================

    def validate_deck(self, card_ids: List[str]) -> tuple[bool, List[str]]:
        """
        Validate a deck list against the card database.
        
        Args:
            card_ids: List of card IDs in the deck
            
        Returns:
            tuple[bool, List[str]]: (is_valid, invalid_cards)
        """
        if not self._loaded:
            raise RuntimeError("CardLoader not loaded. Call load() first.")
        
        invalid_cards = []
        for card_id in card_ids:
            if card_id not in self.cards:
                invalid_cards.append(card_id)
        
        return len(invalid_cards) == 0, invalid_cards

    def is_valid_deck(self, card_ids: List[str]) -> bool:
        """
        Check if a deck is valid (all cards exist).
        
        Args:
            card_ids: List of card IDs in the deck
            
        Returns:
            bool: True if all cards are valid
        """
        valid, _ = self.validate_deck(card_ids)
        return valid

    # ==========================================================
    # Status Methods
    # ==========================================================

    def is_loaded(self) -> bool:
        """Check if the loader has been loaded."""
        return self._loaded

    def count(self) -> int:
        """Return the number of loaded cards."""
        if not self._loaded:
            return 0
        return len(self.cards)

    def clear(self) -> None:
        """Clear all loaded cards."""
        self.cards.clear()
        self._loaded = False

    # ==========================================================
    # Debug Methods
    # ==========================================================

    def print_summary(self) -> None:
        """Print a summary of loaded cards."""
        if not self._loaded:
            print("No cards loaded.")
            return
        
        print(f"\n📊 Card Database Summary:")
        print(f"   Total cards: {len(self.cards)}")
        
        # Count by type
        types = {}
        for card in self.cards.values():
            types[card.card_type] = types.get(card.card_type, 0) + 1
        
        print(f"\n   By Type:")
        for card_type, count in sorted(types.items()):
            print(f"      {card_type}: {count}")
        
        # Count by color
        colors = {}
        for card in self.cards.values():
            for color in card.colors:
                colors[color] = colors.get(color, 0) + 1
        
        print(f"\n   By Color:")
        color_names = {"W": "White", "U": "Blue", "B": "Black", "R": "Red", "G": "Green", "C": "Colorless"}
        for color, count in sorted(colors.items()):
            print(f"      {color_names.get(color, color)}: {count}")


# ==========================================================
# Convenience Functions
# ==========================================================

def load_cards(filename: str = "cards/cards.json") -> Dict[str, Card]:
    """
    Convenience function to load cards.
    
    Args:
        filename: Path to the cards.json file
        
    Returns:
        Dict[str, Card]: Dictionary mapping card_id to Card objects
    """
    loader = CardLoader()
    return loader.load(filename)


# ==========================================================
# Singleton Instance
# ==========================================================

_loader_instance = None

def get_card_loader() -> CardLoader:
    """
    Get the global CardLoader instance (singleton).
    
    Returns:
        CardLoader: The global CardLoader instance
    """
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = CardLoader()
    return _loader_instance