from flask import Flask, request, jsonify, render_template_string, session
import requests
import re

app = Flask(__name__)
app.secret_key = "government-scheme-bot-secret-key"

# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3.2"


# ============================================================
# GOVERNMENT SCHEME KNOWLEDGE BASE
# ============================================================

SCHEMES = [
    {
        "name": "PM-KISAN",
        "category": "Farmers",
        "aliases": [
            "pm kisan",
            "pm-kisan",
            "pmkisan",
            "kisan samman nidhi",
            "pradhan mantri kisan samman nidhi"
        ],
        "description": "PM-KISAN is a government scheme that provides income support to eligible farmer families.",
        "eligibility": "Eligible farmer families who satisfy the scheme requirements can apply.",
        "documents": "Aadhaar, bank account details, land-related records and other documents as required.",
        "benefits": "Financial support is provided to eligible beneficiaries according to the scheme rules.",
        "application": "Application can be made through the official PM-KISAN system and eligible government channels."
    },

    {
        "name": "PM-KUSUM",
        "category": "Farmers",
        "aliases": [
            "pm kusum",
            "pm-kusum",
            "pmkusum",
            "kusum scheme",
            "kisan urja suraksha"
        ],
        "description": "PM-KUSUM promotes the use of solar energy in agriculture, including solar-powered agricultural systems.",
        "eligibility": "Farmers and other eligible groups as specified by the scheme and implementing authorities.",
        "documents": "Identity proof, land details, bank details and documents required by the implementing agency.",
        "benefits": "Supports solar energy adoption for agricultural activities.",
        "application": "Application procedures depend on the state and implementing agency."
    },

    {
        "name": "Soil Health Card Scheme",
        "category": "Farmers",
        "aliases": [
            "soil health card",
            "soil health card scheme",
            "soil card"
        ],
        "description": "The Soil Health Card Scheme provides farmers with information about soil health and nutrient requirements.",
        "eligibility": "Farmers can use the service to understand the condition and nutrient requirements of their agricultural soil.",
        "documents": "Farmer identification and land or field information may be required.",
        "benefits": "Helps farmers make better decisions about fertilizers and soil management.",
        "application": "Farmers can access the service through government agricultural departments and related portals."
    },

    {
        "name": "National Scholarship Portal Schemes",
        "category": "Students",
        "aliases": [
            "national scholarship portal",
            "nsp",
            "student scholarship",
            "scholarship portal",
            "scholarships"
        ],
        "description": "The National Scholarship Portal provides a common platform for various scholarships offered by government departments.",
        "eligibility": "Eligibility depends on the particular scholarship, educational level, income criteria and other conditions.",
        "documents": "Common documents may include Aadhaar, educational certificates, bank details, income certificate and other required documents.",
        "benefits": "Eligible students may receive financial assistance according to the selected scholarship.",
        "application": "Students can apply through the National Scholarship Portal when applications are open."
    },

    {
        "name": "PM Scholarship Scheme",
        "category": "Students",
        "aliases": [
            "pm scholarship",
            "pm scholarship scheme",
            "prime minister scholarship",
            "prime minister scholarship scheme"
        ],
        "description": "The Prime Minister's Scholarship Scheme supports eligible students under specified government eligibility conditions.",
        "eligibility": "Eligibility depends on the specific PM Scholarship Scheme rules and applicant category.",
        "documents": "Educational documents, identity proof, bank details and other documents specified by the scheme.",
        "benefits": "Eligible students may receive scholarship support according to scheme rules.",
        "application": "Applications are generally submitted through the designated government scholarship system."
    },

    {
        "name": "Pradhan Mantri Awas Yojana",
        "category": "Housing",
        "aliases": [
            "pm awas yojana",
            "pmay",
            "pradhan mantri awas yojana",
            "housing scheme",
            "house scheme"
        ],
        "description": "Pradhan Mantri Awas Yojana supports housing for eligible beneficiaries under its different components.",
        "eligibility": "Eligibility depends on the applicable PMAY component, household conditions and government guidelines.",
        "documents": "Identity proof, address details, income-related documents and other documents may be required.",
        "benefits": "Eligible beneficiaries can receive housing-related assistance according to the applicable component.",
        "application": "Application procedures depend on the relevant PMAY component and implementing authority."
    },

    {
        "name": "Ayushman Bharat PM-JAY",
        "category": "Healthcare",
        "aliases": [
            "ayushman bharat",
            "pm jay",
            "pm-jay",
            "pmjay",
            "ayushman bharat pm jay",
            "health insurance scheme"
        ],
        "description": "Ayushman Bharat PM-JAY is a government health protection scheme for eligible beneficiaries.",
        "eligibility": "Eligibility is determined according to the applicable government beneficiary database and scheme rules.",
        "documents": "Identity and beneficiary verification documents may be required.",
        "benefits": "Eligible beneficiaries can receive healthcare coverage according to the scheme rules.",
        "application": "Beneficiary verification and access can be done through authorized government and healthcare channels."
    },

    {
        "name": "PM SVANidhi",
        "category": "Employment",
        "aliases": [
            "pm svanidhi",
            "pm-svanidhi",
            "svanidhi",
            "street vendor scheme",
            "street vendors"
        ],
        "description": "PM SVANidhi supports eligible street vendors through working-capital assistance and related incentives.",
        "eligibility": "Eligible street vendors who satisfy the scheme requirements can apply.",
        "documents": "Identity proof, vendor-related information and other documents required by the authorities.",
        "benefits": "Provides eligible street vendors access to working-capital support under the scheme.",
        "application": "Applications can be made through designated government channels and lending institutions."
    },

    {
        "name": "Pradhan Mantri MUDRA Yojana",
        "category": "Employment",
        "aliases": [
            "mudra",
            "pm mudra",
            "pm mudra yojana",
            "mudra yojana",
            "business loan scheme"
        ],
        "description": "Pradhan Mantri MUDRA Yojana supports eligible small and micro enterprises through institutional credit.",
        "eligibility": "Eligible micro and small business activities can apply subject to lending and scheme requirements.",
        "documents": "Identity proof, address proof, business information and documents requested by the lending institution.",
        "benefits": "Provides access to institutional credit for eligible business activities.",
        "application": "Applications are made through participating banks, financial institutions or other authorized lenders."
    }
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize(text):
    """Convert text into simple searchable form."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_scheme(question):
    """
    Find the most relevant scheme from the user's question.
    Longest alias gets priority.
    """

    q = normalize(question)

    matches = []

    for scheme in SCHEMES:
        all_names = [scheme["name"]] + scheme["aliases"]

        for alias in all_names:
            alias_normalized = normalize(alias)

            if alias_normalized in q:
                matches.append(
                    (len(alias_normalized), scheme)
                )

    if matches:
        matches.sort(key=lambda x: x[0], reverse=True)
        return matches[0][1]

    return None


def detect_category(question):
    """Detect category from normal user questions."""

    q = normalize(question)

    category_keywords = {
        "Farmers": [
            "farmer",
            "farmers",
            "agriculture",
            "agricultural",
            "farming",
            "crop",
            "kisan",
            "farmer scheme"
        ],

        "Students": [
            "student",
            "students",
            "scholarship",
            "scholarships",
            "education",
            "college",
            "school",
            "study"
        ],

        "Housing": [
            "housing",
            "house",
            "home",
            "homes",
            "awas",
            "housing scheme"
        ],

        "Healthcare": [
            "health",
            "healthcare",
            "medical",
            "hospital",
            "health insurance",
            "treatment",
            "ayushman"
        ],

        "Employment": [
            "employment",
            "job",
            "jobs",
            "business",
            "loan",
            "street vendor",
            "self employment",
            "small business"
        ]
    }

    for category, keywords in category_keywords.items():

        for keyword in keywords:

            pattern = r"\b" + re.escape(keyword) + r"\b"

            if re.search(pattern, q):
                return category

    return None


def get_scheme_by_name(name):
    """Find scheme by exact name."""

    for scheme in SCHEMES:

        if scheme["name"] == name:
            return scheme

    return None


def get_category_schemes(category):
    """Return all schemes belonging to a category."""

    return [
        scheme
        for scheme in SCHEMES
        if scheme["category"] == category
    ]


def search_schemes(question):
    """
    Search the knowledge base for relevant schemes.
    """

    q = normalize(question)

    results = []

    for scheme in SCHEMES:

        score = 0

        searchable_text = normalize(
            scheme["name"]
            + " "
            + scheme["category"]
            + " "
            + scheme["description"]
            + " "
            + scheme["eligibility"]
            + " "
            + scheme["benefits"]
            + " "
            + " ".join(scheme["aliases"])
        )

        words = q.split()

        for word in words:

            if len(word) >= 3 and word in searchable_text:
                score += 1

        if score > 0:
            results.append((score, scheme))

    results.sort(key=lambda x: x[0], reverse=True)

    return [scheme for score, scheme in results]


def build_context(question, scheme=None, category=None):
    """
    Build information that will be given to Ollama.
    """

    selected = []

    # 1. Specific scheme
    if scheme:
        selected = [scheme]

    # 2. Category
    elif category:
        selected = get_category_schemes(category)

    # 3. Search
    else:
        selected = search_schemes(question)

    # 4. If still nothing, give all schemes
    if not selected:
        selected = SCHEMES

    context_parts = []

    for item in selected:

        context_parts.append(
            f"""
Scheme: {item['name']}
Category: {item['category']}
Description: {item['description']}
Eligibility: {item['eligibility']}
Documents: {item['documents']}
Benefits: {item['benefits']}
Application: {item['application']}
"""
        )

    return "\n".join(context_parts)


# ============================================================
# OLLAMA AI
# ============================================================

def ask_ai(question, context, conversation):
    """
    Send the user's question to Ollama.
    """

    prompt = f"""
You are a Government Scheme Information Bot for India.

Your job is to answer questions about government schemes clearly and simply.

IMPORTANT RULES:

1. Use the supplied knowledge base as your main source.
2. Do NOT invent scheme details.
3. Do NOT make up eligibility, amounts, dates or documents.
4. If the information is not available, clearly say:
   "I don't have that information in my current knowledge base."
5. If the user asks about a scheme, explain:
   - What it is
   - Who can apply
   - Benefits
   - Documents
   - How to apply
6. If the user asks for schemes in a category, list the relevant schemes.
7. Understand follow-up questions using the conversation history.
8. Keep the answer simple and easy to understand.
9. If the user asks a general question, answer based on the available scheme information.
10. Mention that users should verify current details through official government sources when appropriate.

KNOWLEDGE BASE:
{context}

PREVIOUS CONVERSATION:
{conversation}

USER QUESTION:
{question}

Give a helpful answer.
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        if response.status_code != 200:

            return (
                "Ollama returned an error. "
                "Please make sure Ollama is running and the model "
                f"'{OLLAMA_MODEL}' is installed."
            )

        data = response.json()

        answer = data.get("response", "").strip()

        if not answer:
            return "I could not generate an answer. Please try again."

        return answer

    except requests.exceptions.ConnectionError:

        return (
            "I cannot connect to Ollama.\n\n"
            "Please start Ollama and make sure the model is available.\n\n"
            "Run:\n"
            "ollama run llama3.2"
        )

    except requests.exceptions.Timeout:

        return (
            "The AI took too long to respond. "
            "Please try your question again."
        )

    except Exception as e:

        return f"Error connecting to AI: {str(e)}"


# ============================================================
# MAIN CHAT ROUTE
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "answer": "Please enter a question."
            }), 400

        question = str(data.get("question", "")).strip()

        if not question:

            return jsonify({
                "answer": "Please enter a question."
            }), 400

        # ----------------------------------------------------
        # FIND SCHEME
        # ----------------------------------------------------

        scheme = find_scheme(question)

        # ----------------------------------------------------
        # FIND CATEGORY
        # ----------------------------------------------------

        category = detect_category(question)

        # ----------------------------------------------------
        # FOLLOW-UP MEMORY
        # ----------------------------------------------------

        last_scheme = session.get("last_scheme")

        # If user didn't mention a scheme/category,
        # use the previously discussed scheme.
        if scheme is None and category is None and last_scheme:

            scheme = get_scheme_by_name(last_scheme)

        # ----------------------------------------------------
        # SAVE CURRENT SCHEME
        # ----------------------------------------------------

        if scheme:

            session["last_scheme"] = scheme["name"]

        # ----------------------------------------------------
        # BUILD KNOWLEDGE CONTEXT
        # ----------------------------------------------------

        context = build_context(
            question=question,
            scheme=scheme,
            category=category
        )

        # ----------------------------------------------------
        # CONVERSATION MEMORY
        # ----------------------------------------------------

        conversation = session.get("conversation", [])

        conversation_text = ""

        for message in conversation[-6:]:

            conversation_text += (
                f"{message['role']}: "
                f"{message['text']}\n"
            )

        # ----------------------------------------------------
        # ASK AI
        # ----------------------------------------------------

        answer = ask_ai(
            question=question,
            context=context,
            conversation=conversation_text
        )

        # ----------------------------------------------------
        # SAVE CONVERSATION
        # ----------------------------------------------------

        conversation.append({
            "role": "User",
            "text": question
        })

        conversation.append({
            "role": "Assistant",
            "text": answer
        })

        # Keep only recent messages
        session["conversation"] = conversation[-12:]

        return jsonify({
            "answer": answer
        })

    except Exception as e:

        return jsonify({
            "answer": f"Server error: {str(e)}"
        }), 500


# ============================================================
# CLEAR CHAT
# ============================================================

@app.route("/clear", methods=["POST"])
def clear_chat():

    session.pop("conversation", None)
    session.pop("last_scheme", None)

    return jsonify({
        "success": True
    })


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template_string("""

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Government Scheme Information Bot</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background:
        linear-gradient(
            135deg,
            #eef5ff,
            #f8fbff
        );

    color: #1f2937;
}


/* =========================================================
   HEADER
   ========================================================= */

.header {

    background:
        linear-gradient(
            135deg,
            #0f4c81,
            #2563eb
        );

    color: white;

    padding: 28px 20px;

    text-align: center;

}

.header h1 {

    margin: 0;

    font-size: 30px;

}

.header p {

    margin-top: 8px;

    font-size: 16px;

    opacity: 0.9;

}


/* =========================================================
   MAIN
   ========================================================= */

.container {

    width: 92%;

    max-width: 1200px;

    margin: 25px auto;

}


/* =========================================================
   CATEGORY CARDS
   ========================================================= */

.category-grid {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(210px, 1fr)
        );

    gap: 18px;

    margin-bottom: 25px;

}


.category-card {

    background: white;

    border-radius: 18px;

    padding: 20px;

    box-shadow:
        0 5px 20px
        rgba(0,0,0,0.08);

    transition: 0.2s;

}


.category-card:hover {

    transform: translateY(-3px);

}


.category-title {

    font-size: 20px;

    font-weight: bold;

    margin-bottom: 15px;

}


/* =========================================================
   SCHEME BUTTONS
   ========================================================= */

.scheme-btn {

    display: block;

    width: 100%;

    border: none;

    background: #eef5ff;

    color: #174ea6;

    padding: 10px;

    margin-top: 8px;

    border-radius: 10px;

    cursor: pointer;

    text-align: left;

    font-size: 14px;

}

.scheme-btn:hover {

    background: #dbeafe;

}


/* =========================================================
   CHAT BOX
   ========================================================= */

.chat-container {

    background: white;

    border-radius: 18px;

    box-shadow:
        0 5px 20px
        rgba(0,0,0,0.08);

    overflow: hidden;

}


.chat-header {

    background: #0f4c81;

    color: white;

    padding: 16px 20px;

    display: flex;

    justify-content: space-between;

    align-items: center;

}


.chat-header h2 {

    margin: 0;

    font-size: 20px;

}


.clear-btn {

    border: none;

    background: white;

    color: #0f4c81;

    padding: 8px 14px;

    border-radius: 8px;

    cursor: pointer;

    font-weight: bold;

}


/* =========================================================
   MESSAGES
   ========================================================= */

.messages {

    height: 450px;

    overflow-y: auto;

    padding: 20px;

    background: #f8fafc;

}


.message {

    max-width: 80%;

    padding: 13px 16px;

    border-radius: 14px;

    margin-bottom: 12px;

    white-space: pre-wrap;

    line-height: 1.5;

}


.user {

    margin-left: auto;

    background: #2563eb;

    color: white;

    border-bottom-right-radius: 4px;

}


.bot {

    margin-right: auto;

    background: white;

    color: #1f2937;

    border: 1px solid #e5e7eb;

    border-bottom-left-radius: 4px;

}


/* =========================================================
   SEARCH BAR
   ========================================================= */

.search-area {

    display: flex;

    gap: 10px;

    padding: 15px;

    border-top: 1px solid #e5e7eb;

    background: white;

}


.search-input {

    flex: 1;

    padding: 14px;

    border: 1px solid #cbd5e1;

    border-radius: 12px;

    font-size: 15px;

    outline: none;

}


.search-input:focus {

    border-color: #2563eb;

}


.send-btn {

    border: none;

    background: #2563eb;

    color: white;

    padding: 0 22px;

    border-radius: 12px;

    cursor: pointer;

    font-weight: bold;

}


.send-btn:hover {

    background: #1d4ed8;

}


.send-btn:disabled {

    background: #94a3b8;

    cursor: not-allowed;

}


/* =========================================================
   MOBILE
   ========================================================= */

@media(max-width:600px) {

    .header h1 {
        font-size: 23px;
    }

    .messages {
        height: 400px;
    }

    .message {
        max-width: 90%;
    }

    .search-area {
        flex-direction: column;
    }

    .send-btn {
        height: 45px;
    }

}

</style>

</head>


<body>


<div class="header">

    <h1>🇮🇳 Government Scheme Information Bot</h1>

    <p>
        Find information about Indian Government Schemes
    </p>

</div>


<div class="container">


    <!-- =====================================================
         CATEGORY SECTION
         ===================================================== -->

    <div class="category-grid">


        <!-- FARMERS -->

        <div class="category-card">

            <div class="category-title">
                👨‍🌾 Farmers
            </div>

            <button
                class="scheme-btn"
                onclick="askScheme('PM-KISAN')">

                PM-KISAN

            </button>

            <button
                class="scheme-btn"
                onclick="askScheme('PM-KUSUM')">

                PM-KUSUM

            </button>

            <button
                class="scheme-btn"
                onclick="askScheme('Soil Health Card Scheme')">

                Soil Health Card

            </button>

        </div>


        <!-- STUDENTS -->

        <div class="category-card">

            <div class="category-title">
                🎓 Students
            </div>

            <button
                class="scheme-btn"
                onclick="askScheme('National Scholarship Portal Schemes')">

                National Scholarship Portal

            </button>

            <button
                class="scheme-btn"
                onclick="askScheme('PM Scholarship Scheme')">

                PM Scholarship Scheme

            </button>

        </div>


        <!-- HOUSING -->

        <div class="category-card">

            <div class="category-title">
                🏠 Housing
            </div>

            <button
                class="scheme-btn"
                onclick="askScheme('Pradhan Mantri Awas Yojana')">

                Pradhan Mantri Awas Yojana

            </button>

        </div>


        <!-- HEALTHCARE -->

        <div class="category-card">

            <div class="category-title">
                🏥 Healthcare
            </div>

            <button
                class="scheme-btn"
                onclick="askScheme('Ayushman Bharat PM-JAY')">

                Ayushman Bharat PM-JAY

            </button>

        </div>


        <!-- EMPLOYMENT -->

        <div class="category-card">

            <div class="category-title">
                💼 Employment
            </div>

            <button
                class="scheme-btn"
                onclick="askScheme('PM SVANidhi')">

                PM SVANidhi

            </button>

            <button
                class="scheme-btn"
                onclick="askScheme('Pradhan Mantri MUDRA Yojana')">

                PM MUDRA

            </button>

        </div>


    </div>


    <!-- =====================================================
         CHAT
         ===================================================== -->

    <div class="chat-container">


        <div class="chat-header">

            <h2>🤖 Scheme Assistant</h2>

            <button
                class="clear-btn"
                onclick="clearChat()">

                Clear Chat

            </button>

        </div>


        <div
            id="messages"
            class="messages">

            <div class="message bot">

                👋 Hello!

                I am the Government Scheme Information Bot.

                You can:

                • Select a scheme above
                • Ask about farmers
                • Ask about scholarships
                • Ask about housing
                • Ask about healthcare
                • Ask about employment
                • Type any question in the search bar

                Try:

                "What government schemes are available for farmers?"

            </div>

        </div>


        <!-- =================================================
             SEARCH BAR
             ================================================= -->

        <div class="search-area">

            <input
                id="question"
                class="search-input"
                type="text"
                placeholder="Ask anything about government schemes..."
                autocomplete="off"
            >

            <button
                id="sendButton"
                class="send-btn"
                onclick="sendMessage()">

                Send

            </button>

        </div>


    </div>


</div>


<script>


// ============================================================
// ADD MESSAGE
// ============================================================

function addMessage(text, type) {

    const messages =
        document.getElementById("messages");

    const div =
        document.createElement("div");

    div.className =
        "message " + type;

    div.textContent = text;

    messages.appendChild(div);

    messages.scrollTop =
        messages.scrollHeight;

}


// ============================================================
// SEND MESSAGE
// ============================================================

async function sendMessage() {

    const input =
        document.getElementById("question");

    const button =
        document.getElementById("sendButton");

    const question =
        input.value.trim();


    if (!question) {

        return;

    }


    // Show user's message

    addMessage(
        question,
        "user"
    );


    // Clear input

    input.value = "";


    // Disable button

    button.disabled = true;

    button.textContent = "Thinking...";


    // Temporary loading message

    const loading =
        document.createElement("div");

    loading.className =
        "message bot";

    loading.textContent =
        "Thinking...";

    loading.id =
        "loading-message";

    document
        .getElementById("messages")
        .appendChild(loading);


    try {

        const response =
            await fetch(
                "/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        question: question
                    })
                }
            );


        // Remove loading message

        const loadingMessage =
            document.getElementById(
                "loading-message"
            );

        if (loadingMessage) {

            loadingMessage.remove();

        }


        // Try to read JSON

        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.answer ||
                "Server error"
            );

        }


        addMessage(
            data.answer ||
            "No answer received.",
            "bot"
        );


    }

    catch (error) {

        const loadingMessage =
            document.getElementById(
                "loading-message"
            );

        if (loadingMessage) {

            loadingMessage.remove();

        }


        addMessage(
            "❌ " + error.message,
            "bot"
        );

    }

    finally {

        button.disabled = false;

        button.textContent = "Send";

        input.focus();

    }

}


// ============================================================
// ASK SCHEME
// ============================================================

function askScheme(schemeName) {

    const input =
        document.getElementById("question");

    input.value =
        "Tell me about " + schemeName;

    sendMessage();

}


// ============================================================
// ENTER KEY
// ============================================================

document
    .getElementById("question")
    .addEventListener(
        "keydown",
        function(event) {

            if (event.key === "Enter") {

                event.preventDefault();

                sendMessage();

            }

        }
    );


// ============================================================
// CLEAR CHAT
// ============================================================

async function clearChat() {

    try {

        await fetch(
            "/clear",
            {
                method: "POST"
            }
        );

    } catch (error) {

        console.log(error);

    }


    document
        .getElementById("messages")
        .innerHTML = "";


    addMessage(
        "Chat cleared. 👋 Ask me about any government scheme.",
        "bot"
    );

}

</script>


</body>

</html>

""")


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print("🇮🇳 Government Scheme Information Bot")

    print("=" * 60)

    print("Ollama Model:", OLLAMA_MODEL)

    print("Open browser at:")

    print("http://127.0.0.1:5000")

    print("=" * 60)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )