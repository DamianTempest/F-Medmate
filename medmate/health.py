"""Conservative offline information, food metadata and authoritative links."""
import re
from .store import ValidationError

RESOURCES = [
    ('Healthy eating','WHO guidance on varied, balanced diets.','https://www.who.int/news-room/fact-sheets/detail/healthy-diet','food-apple-outline'),
    ('Health topics','Browse WHO information by health topic.','https://www.who.int/health-topics','book-open-page-variant-outline'),
    ('Research library','Search biomedical publications on PubMed.','https://pubmed.ncbi.nlm.nih.gov/','microscope'),
    ('Health news','Visit the WHO newsroom for current updates.','https://www.who.int/news-room','newspaper-variant-outline'),
    ('Chest pain information','NHS information on warning signs and seeking urgent help.','https://www.nhs.uk/symptoms/chest-pain/','heart-pulse'),
]
TIPS = [
    'Build meals around a variety of vegetables, fruits, legumes and whole grains.',
    'Write down your questions before a health appointment.',
    'Keep an up-to-date list of medicines and allergies for your clinician.',
    'Keep a regular sleep routine and make time to wind down.',
    'Move regularly in a way that suits your ability and health needs.',
]
# These describe specific preparation variants, never all versions of a dish.
MEALS = [
    {'name':'Red red with plantain','diet':'Vegan','ingredients':['cowpeas','plantain','tomato','onion','vegetable oil'], 'allergens':[], 'method':'Cook the cowpeas with tomato and onion. Serve with baked or boiled plantain.'},
    {'name':'Vegetable jollof','diet':'Vegan','ingredients':['rice','tomato','onion','carrot','peas','vegetable oil'], 'allergens':[], 'method':'Cook rice in a tomato base, then add vegetables. Use plant-based stock.'},
    {'name':'Kontomire with boiled yam','diet':'Vegan','ingredients':['cocoyam leaves','yam','tomato','onion','vegetable oil'], 'allergens':[], 'method':'Prepare this version without fish, meat, eggs or groundnuts. Serve with boiled yam.'},
    {'name':'Tubaani with tomato sauce','diet':'Vegan','ingredients':['cowpeas','tomato','onion','vegetable oil'], 'allergens':[], 'method':'Steam blended cowpeas and serve with a simple tomato and onion sauce.'},
    {'name':'Groundnut soup with rice','diet':'Vegan','ingredients':['peanuts','rice','tomato','onion','vegetable stock'], 'allergens':['peanut'], 'method':'Use a plant-based soup preparation. Groundnuts are peanuts; avoid this dish if allergic.'},
    {'name':'Boiled yam with egg stew','diet':'Vegetarian','ingredients':['yam','egg','tomato','onion','vegetable oil'], 'allergens':['egg'], 'method':'Cook the eggs in tomato stew and serve with boiled yam. Do not add fish or meat.'},
    {'name':'Grilled tilapia with vegetables','diet':'Pescatarian','ingredients':['fish','tomato','onion','cabbage','carrot','rice'], 'allergens':['fish'], 'method':'Grill the fish and serve with cooked rice and vegetables.'},
    {'name':'Chicken with vegetable rice','diet':'Omnivore','ingredients':['chicken','rice','carrot','peas','onion','vegetable oil'], 'allergens':[], 'method':'Cook chicken thoroughly and serve with rice and vegetables.'},
]
ALIASES = {
    'nuts':{'peanut','tree nut'}, 'nut':{'peanut','tree nut'},
    'peanuts':{'peanut'},'peanut':{'peanut'},'groundnuts':{'peanut'},'groundnut':{'peanut'},
    'tree nuts':{'tree nut'},'tree nut':{'tree nut'},'fish':{'fish'},
    'eggs':{'egg'},'egg':{'egg'},'milk':{'milk'},'dairy':{'milk'},
    'soy':{'soy'},'soya':{'soy'},'wheat':{'wheat'},'gluten':{'wheat','barley','rye'},
    'shellfish':{'shellfish'},'sesame':{'sesame'},'none':set(), 'no allergies':set(),
}

def meal_ideas(preference,allergies):
    allowed={'Vegan':{'Vegan'},'Vegetarian':{'Vegan','Vegetarian'},'Pescatarian':{'Vegan','Vegetarian','Pescatarian'},'Omnivore':{'Vegan','Vegetarian','Pescatarian','Omnivore'}}
    if preference not in allowed: raise ValidationError('Choose a listed dietary preference.')
    avoid=set()
    for token in re.split(r'[,;\n]',allergies.lower()):
        token=token.strip()
        if not token: continue
        if token not in ALIASES: raise ValidationError(f'We do not recognise "{token}". Ask a dietitian to review ingredients; no allergy suitability can be confirmed.')
        avoid.update(ALIASES[token])
    return [dict(m) for m in MEALS if m['diet'] in allowed[preference] and not avoid.intersection(m['allergens'])]

def symptom_guidance(text):
    if not text.strip(): raise ValidationError('Describe your symptoms first.')
    # Always show the emergency information. A keyword check is not a triage tool.
    return ('This tool cannot diagnose a condition or decide how urgent it is.\n\n'
            'Seek emergency care now if you have severe difficulty breathing, sudden persistent chest pain, '
            'collapse, or other life-threatening symptoms. Contact your local emergency service; do not wait for a reply here.\n\n'
            'For other concerns, contact a clinician, particularly if symptoms are worsening or persistent. '
            'Write down when they started, their severity, any changes, medicines taken, and relevant medical history. '
            'Use Appointments to arrange a local prototype request.\n\n'
            'Source: NHS chest pain and heart attack information. This offline page does not assess your individual symptoms.')

def offline_answer(text):
    if not text.strip(): raise ValidationError('Enter a question first.')
    lower=text.lower()
    prefix='Offline information library (not AI)\n\n'
    if any(w in lower for w in ('medicine','dose','diagnos','malaria','pain','fever','symptom','pregnan')):
        return prefix+'A clinician or pharmacist needs to assess your circumstances before recommending treatment. Use Symptom guidance to prepare your concerns and My care to contact a doctor account on this device. This library cannot diagnose or prescribe.'
    if any(w in lower for w in ('food','diet','eat','meal','nutrition')):
        return prefix+'Choose varied meals with vegetables, fruits, legumes and whole grains. Open Meal ideas for Ghanaian preparation suggestions with ingredient lists. Individual dietary needs differ; discuss medical dietary requirements with a dietitian. Source: WHO Healthy diet.'
    if any(w in lower for w in ('sleep','rest')):
        return prefix+'Keep a regular sleep routine and set aside time to wind down. If sleep problems persist, discuss them with a clinician.'
    if any(w in lower for w in ('appointment','doctor','profile','message')):
        return prefix+'Open My care to link a doctor account on this device, then request an appointment or send a message. Save your details in My profile. Online AI can be configured in Settings.'
    return prefix+'I can show general information about meals, sleep, preparing for appointments, and using Medmate. For a personal health concern, contact a clinician. For open-ended AI responses, configure an OpenRouter key and model, then enable Online AI in Settings.'
