#!/usr/bin/env python
import streamlit as st
import asyncio
import os
from pathlib import Path
import sys

from mistralai import Mistral
from mistralai.extra.run.context import RunContext
from mcp import StdioServerParameters
from mistralai.extra.mcp.stdio import MCPClientSTDIO
from mistralai.types import BaseModel

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Interface Kimble Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre principal
st.title("🤖 Interface MCP Client - Kimble Agent")
st.markdown("---")

# Configuration dans la barre latérale
st.sidebar.header("⚙️ Configuration")

# Champ pour la clé API Mistral
api_key = st.sidebar.text_input(
    "Clé API Mistral",
    type="password",
    value="jA5RKAngtM3YOCBd5UhOp2QI62WwIUcJ",
    help="Entrez votre clé API Mistral"
)

# Champ pour le chemin vers le script de l'agent
agent_script_path = st.sidebar.text_input(
    "Chemin vers le script de l'agent",
    value="mcp_server.py",
    help="Chemin relatif ou absolu vers le script de l'agent sales"
)

# Sélection du modèle
model_options = [
    "mistral-medium-latest",
    "mistral-large-latest",
    "mistral-small-latest"
]
selected_model = st.sidebar.selectbox(
    "Modèle Mistral",
    options=model_options,
    index=0
)


# Définition de la classe de résultat
class ProductResult(BaseModel):
    result: str


# Fonction asynchrone pour interagir avec l'agent MCP
async def interact_with_agent(user_input: str, api_key: str, model: str, script_path: str):
    client = None
    try:
        # Initialiser le client Mistral avec un timeout
        client = Mistral(api_key=api_key)

        # Obtenir le répertoire de travail actuel
        cwd = Path(__file__).parent
        script_full_path = (cwd / script_path).resolve()

        if not script_full_path.exists():
            return f"Erreur: Le fichier de script '{script_full_path}' est introuvable."

        # Définir les paramètres du serveur MCP local
        server_params = StdioServerParameters(
            command=sys.executable,  # Utiliser le même interpréteur Python
            args=[str(script_full_path)],
            env=os.environ.copy(),
        )

        # Créer un agent pour interagir avec Kimble
        kimble_agent = client.beta.agents.create(
            model=model,
            name="Kimble agent",
            instructions='''
                You are a helpful HR assistant that helps users manage their HR tasks.
                You have access to Kimble HR system through the available tools.

                Guidelines:
                1. Be concise and professional
                2. Only use tools when necessary
                3. Verify inputs before execution
                4. Handle errors gracefully''',
            description="HR assistant for Kimble HR system",
        )

        # Créer un contexte d'exécution pour l'agent
        async with RunContext(
                agent_id=kimble_agent.id,
                output_format=ProductResult,
                continue_on_fn_error=True,
        ) as run_ctx:
            # Créer et enregistrer un client MCP avec le contexte d'exécution
            mcp_client = MCPClientSTDIO(stdio_params=server_params)
            try:
                await run_ctx.register_mcp_client(mcp_client=mcp_client)

                # Exécuter la conversation avec l'agent
                run_result = await client.beta.conversations.run_async(
                    run_ctx=run_ctx,
                    inputs=user_input,
                )

                return run_result.output_as_model.result
            finally:
                # Ensure MCP client is properly closed
                if hasattr(mcp_client, 'close'):
                    try:
                        await mcp_client.close()
                    except Exception as e:
                        print(f"Error closing MCP client: {e}")

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in interact_with_agent: {error_trace}")
        return f"Erreur lors de l'interaction avec l'agent: {str(e)}"
    finally:
        # Nettoyer les ressources du client si nécessaire
        if client is not None:
            try:
                await client.close()
            except Exception as e:
                print(f"Error closing Mistral client: {e}")


# Fonction wrapper pour exécuter le code asynchrone
def run_async_interaction(user_input: str, api_key: str, model: str, script_path: str):
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the async function in the new event loop
        result = loop.run_until_complete(
            interact_with_agent(user_input, api_key, model, script_path)
        )
        return result
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in run_async_interaction: {error_trace}")
        return f"Erreur lors de l'exécution: {str(e)}"
    finally:
        # Clean up the event loop
        try:
            # Cancel all running tasks
            pending = asyncio.all_tasks(loop=loop)
            for task in pending:
                task.cancel()
                try:
                    loop.run_until_complete(task)
                except (asyncio.CancelledError, Exception):
                    pass
            
            # Run remaining tasks that were created during cleanup
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
        finally:
            # Close the loop
            asyncio.set_event_loop(None)
            loop.close()


# Interface principale
st.header("💬 Conversation avec l'Agent Kimble")

# Initialiser l'historique de conversation dans la session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Afficher l'historique des messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie pour les messages
if prompt := st.chat_input("Tapez votre message ici..."):
    # Ajouter le message de l'utilisateur à l'historique
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Vérifier que la clé API est fournie
    if not api_key:
        st.error("Veuillez fournir une clé API Mistral dans la barre latérale.")
    else:
        # Afficher un indicateur de chargement
        with st.chat_message("assistant"):
            with st.spinner("L'agent traite votre demande..."):
                # Obtenir la réponse de l'agent
                response = run_async_interaction(prompt, api_key, selected_model, agent_script_path)
                st.markdown(response)

        # Ajouter la réponse à l'historique
        st.session_state.messages.append({"role": "assistant", "content": response})

# Bouton pour effacer l'historique
if st.sidebar.button("🗑️ Effacer l'historique"):
    st.session_state.messages = []
    st.rerun()

# Informations sur l'application
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ À propos")
st.sidebar.markdown("""
Cette interface permet d'interagir avec un agent MCP (Model Context Protocol) 
qui se connecte au système Kimble

**Fonctionnalités:**
- Interface de chat intuitive
- Configuration flexible des paramètres
- Historique des conversations
- Support pour différents modèles Mistral
""")

# Instructions d'utilisation
with st.expander("📖 Instructions d'utilisation"):
    st.markdown("""
    1. **Configuration**: Assurez-vous que la clé API Mistral et le chemin vers le script de l'agent sont corrects dans la barre latérale.

    2. **Conversation**: Tapez votre message dans la zone de saisie en bas de la page et appuyez sur Entrée.

    3. **Agent Sales**: L'agent peut vous aider avec diverses tâches liées aux ventes dans Odoo ERP, comme:
       - Rechercher des produits
       - Créer des devis
       - Consulter des informations clients
       - Gérer les commandes

    4. **Historique**: Toutes vos conversations sont sauvegardées pendant la session. Utilisez le bouton "Effacer l'historique" pour recommencer.
    """)

