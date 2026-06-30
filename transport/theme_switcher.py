import os

file_path = r'c:\TRANSPORT WORKING_TESTING\transport\templates\track_delivery.html'

with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace CSS variables to switch to Light Theme
replacements = {
    '--bg: #0f172a;': '--bg: #f8f9fa;',
    '--card-bg: #1e293b;': '--card-bg: #ffffff;',
    '--card-border: rgba(255, 255, 255, 0.08);': '--card-border: #eeeeee;',
    '--text: #f1f5f9;': '--text: #333333;',
    '--text-muted: #94a3b8;': '--text-muted: #7f8c8d;',
    '--primary: #f59e0b;': '--primary: #ffd700;',
    '--primary-dark: #d97706;': '--primary-dark: #e6c200;',
    '--secondary: #1e293b;': '--secondary: #1a1a1a;',
    
    # Remove dark gradients and backgrounds
    'background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);': 'background: #ffffff; box-shadow: 0 5px 15px rgba(0,0,0,0.03);',
    'background: rgba(30, 41, 59, 0.95);': 'background: #ffffff; box-shadow: 0 2px 10px rgba(0,0,0,0.05);',
    'background: rgba(255, 255, 255, 0.05);': 'background: #f0f0f0;',
    'border: 2px solid rgba(255, 255, 255, 0.1);': 'border: 2px solid #e0e0e0;',
    'background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(30, 41, 59, 1) 100%);': 'background: #ffffff; border: 1px solid #eeeeee; box-shadow: 0 5px 15px rgba(0,0,0,0.03);',
    'border: 1px solid rgba(59, 130, 246, 0.2);': 'border: 1px solid #eeeeee;',
    'background: linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(30, 41, 59, 1) 100%);': 'background: #ffffff; border: 1px solid #eeeeee; box-shadow: 0 5px 15px rgba(0,0,0,0.03);',
    'background: rgba(0, 0, 0, 0.2);': 'background: #fafbfc; border-top: 1px solid #eeeeee;'
}

for old, new in replacements.items():
    text = text.replace(old, new)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("CSS transformed to light theme.")
