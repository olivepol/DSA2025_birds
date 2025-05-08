"""
Script to transform and enrich course data from raw JSON into a structured and augmented DataFrame
for downstream application use. Translations and transformations are applied directly via mapping.
"""

import json
import pandas as pd
import numpy as np
import ast
from tqdm import tqdm
from deep_translator import GoogleTranslator

# ============================
# Step 1: Load source data from JSON
# ============================
with open('/DSA2025_birds/depreciated_data_prep/courses.json', encoding="utf-8") as f:
    data = json.load(f)

veranstaltung_list = data['veranstaltungen']['veranstaltung']
df_german = pd.json_normalize(veranstaltung_list, sep='_')

# ============================
# Step 2: Define German → English column mapping
# ============================
column_translation = {
    'guid': 'guid',
    'nummer': 'course_number',
    'name': 'course_name',
    'untertitel': 'course_subtitle',
    'bezirk': 'district',
    'veranstaltungsart': 'event_type',
    'minimale_teilnehmerzahl': 'minimum_participants',
    'aktuelle_teilnehmerzahl': 'current_participants',
    'maximale_teilnehmerzahl': 'maximum_participants',
    'anzahl_termine': 'number_of_sessions',
    'beginn_datum': 'start_date',
    'ende_datum': 'end_date',
    'zielgruppe': 'target_group',
    'schlagwort': 'keywords',
    'text': 'description',
    'dvv_kategorie_#text': 'category_label',
    'anmeldung_telefon': 'registration_phone',
    'anmeldung_mail': 'registration_email',
    'anmeldung_link': 'registration_link',
    'ansprechperson_anrede': 'contact_person_salutation',
    'ansprechperson_titel': 'contact_person_title',
    'ansprechperson_name': 'contact_person_last_name',
    'ansprechperson_vorname': 'contact_person_first_name',
    'ansprechperson_telefon': 'contact_person_phone',
    'ansprechperson_mail': 'contact_person_email',
    'preis_betrag': 'price_amount',
    'preis_rabatt_moeglich': 'price_discount_possible',
    'preis_zusatz': 'price_additional',
    'dozent_anrede': 'lecturer_salutation',
    'dozent_titel': 'lecturer_title',
    'dozent_name': 'lecturer_last_name',
    'dozent_vorname': 'lecturer_first_name',
    'ortetermine_adresse_plz': 'locations_address_postal_code',
    'ortetermine_adresse_ort': 'locations_address_city',
    'ortetermine_adresse_strasse': 'locations_address_street',
    'ortetermine_adresse_raum': 'locations_address_room',
    'ortetermine_adresse_laengengrad': 'locations_address_longitude',
    'ortetermine_adresse_breitengrad': 'locations_address_latitude',
    'ortetermine_adresse_behindertenzugang': 'locations_address_accessible',
    'ortetermine_termin_wochentag': 'locations_appointments_weekday',
    'ortetermine_termin_beginn_datum': 'locations_appointments_start_date',
    'ortetermine_termin_beginn_uhrzeit': 'locations_appointments_start_time',
    'ortetermine_termin_ende_uhrzeit': 'locations_appointments_end_time'
}

# ============================
# Step 3: Translate and clean up DataFrame
# ============================
available_cols = [col for col in column_translation if col in df_german.columns]
df_translated = df_german[available_cols].rename(columns={k: column_translation[k] for k in available_cols})

# Add original German course name
df_translated['course_name_german'] = df_german['name']

# Ensure numeric types
for col in ['maximum_participants', 'minimum_participants', 'current_participants']:
    df_translated[col] = pd.to_numeric(df_translated[col], errors='coerce')

# ============================
# Step 4: Add derived metrics
# ============================
df_translated['prop_occupancy_left'] = (
    (df_translated['maximum_participants'] - df_translated['current_participants']) /
    df_translated['maximum_participants']
)

df_translated['prop_minimum_to_reach'] = (
    (df_translated['minimum_participants'] - df_translated['current_participants']) /
    df_translated['minimum_participants']
).clip(lower=0)

# Simulate gender distribution
np.random.seed(42)
df_translated['number_of_women'] = df_translated['current_participants'].apply(
    lambda x: np.random.randint(0, x + 1) if x > 0 else 0)
df_translated['percent_women'] = np.where(df_translated['current_participants'] > 0,
                                          df_translated['number_of_women'] / df_translated['current_participants'], 0)
df_translated['prop_men'] = 1 - df_translated['percent_women']

# Additional flags
df_translated['sponsored'] = np.random.choice([1, 0], size=len(df_translated), p=[0.25, 0.75])
df_translated['gap_to_80_percent_women'] = 0.8 - df_translated['percent_women']
df_translated['gap_to_80_percent_men'] = 0.8 - df_translated['prop_men']

# ============================
# Step 5: Target group encoding
# ============================
if 'target_group' in df_translated.columns:
    df_translated['target_group_raw'] = df_translated['target_group']
    for group in df_translated['target_group_raw'].dropna().unique():
        col_name = f"target_group_{group}"
        df_translated[col_name] = df_translated['target_group_raw'].apply(lambda x: 1 if x == group else 0)

# ============================
# Step 6: Clean and concatenate search text
# ============================
def safe_parse(x):
    try:
        return ast.literal_eval(x) if isinstance(x, str) else x
    except:
        return x

def flatten_keywords(x):
    x = safe_parse(x)
    if isinstance(x, list):
        return ', '.join(map(str, x))
    return str(x)

df_translated['keywords_clean'] = df_translated['keywords'].apply(flatten_keywords)
df_translated['search_text'] = (
    df_translated['course_name_german'].fillna('') + ' ' +
    df_translated['course_subtitle'].fillna('') + ' ' +
    df_translated['keywords_clean'].fillna('')
)

# ============================
# Step 7: Translate course names (German → English)
# ============================
def translate_to_english(text):
    try:
        if pd.isna(text):
            return None
        return GoogleTranslator(source='de', target='en').translate(text)
    except Exception:
        return None

unique_names = df_translated['course_name_german'].dropna().unique()
translation_map = {name: translate_to_english(name) for name in tqdm(unique_names)}
df_translated['course_name_translated'] = df_translated['course_name_german'].map(translation_map)

# ============================
# Step 8: Remove full courses
# ============================
df_final = df_translated[df_translated['prop_occupancy_left'] > 0].copy()
