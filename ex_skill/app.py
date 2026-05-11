from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import json

app = Flask(__name__)
app.secret_key = 'ex_skill_secret_key'

from .persona_generator import PersonaGenerator
from .chat_simulator import ChatSimulator
from .config import PERSONALITY_TYPES, ATTACHMENT_STYLES, FIGHTING_STYLES, MEMORY_TAGS

persona_generator = PersonaGenerator()
active_sessions = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['GET', 'POST'])
def create_persona():
    if request.method == 'POST':
        name = request.form['name']
        personality = request.form['personality']
        attachment = request.form['attachment']
        fighting = request.form['fighting']
        
        memories = []
        for i in range(1, 6):
            memory_tag = request.form.get(f'memory_tag_{i}')
            memory_content = request.form.get(f'memory_content_{i}')
            if memory_tag and memory_content:
                memories.append({"tag": memory_tag, "content": memory_content})
        
        chat_history = []
        chat_text = request.form.get('chat_history', '')
        if chat_text:
            lines = chat_text.split('\n')
            for line in lines:
                if line.strip():
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        chat_history.append({
                            "sender": parts[0].strip(),
                            "content": parts[1].strip()
                        })
        
        persona = persona_generator.create_persona(
            name=name,
            personality_type=personality,
            attachment_style=attachment,
            fighting_style=fighting,
            memories=memories,
            chat_history=chat_history
        )
        
        return redirect(url_for('chat', persona_id=persona['id']))
    
    return render_template('create.html',
                          personalities=PERSONALITY_TYPES,
                          attachments=ATTACHMENT_STYLES,
                          fightings=FIGHTING_STYLES,
                          memory_tags=MEMORY_TAGS)

@app.route('/personas')
def list_personas():
    personas = persona_generator.get_all_personas()
    return render_template('personas.html', personas=personas)

@app.route('/chat/<persona_id>')
def chat(persona_id):
    persona = persona_generator.get_persona(persona_id)
    if not persona:
        return redirect(url_for('list_personas'))
    
    if persona_id not in active_sessions:
        active_sessions[persona_id] = ChatSimulator(persona)
    
    return render_template('chat.html', persona=persona)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json()
    persona_id = data['persona_id']
    user_message = data['message']
    
    if persona_id not in active_sessions:
        persona = persona_generator.get_persona(persona_id)
        if not persona:
            return jsonify({"error": "Persona not found"}), 404
        active_sessions[persona_id] = ChatSimulator(persona)
    
    simulator = active_sessions[persona_id]
    response = simulator.generate_response(user_message)
    
    return jsonify({"response": response})

@app.route('/api/toggle_fighting', methods=['POST'])
def toggle_fighting():
    data = request.get_json()
    persona_id = data['persona_id']
    enabled = data.get('enabled', False)
    
    if persona_id in active_sessions:
        active_sessions[persona_id].toggle_fighting_mode(enabled)
        return jsonify({"success": True})
    
    return jsonify({"error": "Session not found"}), 404

@app.route('/api/add_memory', methods=['POST'])
def add_memory():
    data = request.get_json()
    persona_id = data['persona_id']
    memory = {"tag": data['tag'], "content": data['content']}
    
    if persona_id in active_sessions:
        active_sessions[persona_id].add_memory(memory)
        return jsonify({"success": True})
    
    return jsonify({"error": "Session not found"}), 404

@app.route('/delete/<persona_id>')
def delete_persona(persona_id):
    persona_generator.delete_persona(persona_id)
    if persona_id in active_sessions:
        del active_sessions[persona_id]
    return redirect(url_for('list_personas'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)