import pytest
from medmate.health import meal_ideas, symptom_guidance, offline_answer
from medmate.store import ValidationError

def test_vegan_food_has_no_animal_ingredients():
    meals=meal_ideas('Vegan','')
    assert meals
    assert all(m['diet']=='Vegan' for m in meals)
    assert not any('fish' in m['ingredients'] or 'chicken' in m['ingredients'] for m in meals)

def test_nuts_alias_filters_groundnuts():
    meals=meal_ideas('Omnivore','nuts, fish')
    assert meals
    assert all(not set(m['allergens']) & {'peanut','tree nut','fish'} for m in meals)

def test_unknown_allergy_requires_manual_review():
    with pytest.raises(ValidationError,match='recognise'): meal_ideas('Vegan','mango')

def test_empty_and_unsupported_preferences_rejected():
    with pytest.raises(ValidationError): meal_ideas('Keto','')
    with pytest.raises(ValidationError): symptom_guidance('')

def test_symptom_guidance_never_claims_diagnosis():
    assert 'emergency' in symptom_guidance('chest pain and cannot breathe').lower()
    assert 'diagnose' in symptom_guidance('a sore throat').lower()
    assert 'not reported' not in symptom_guidance('no chest pain').lower()

def test_offline_answer_is_honest_about_limitations():
    assert 'Offline' in offline_answer('How do I sleep better?')
    assert 'clinician' in offline_answer('Which medicine for malaria?').lower()
