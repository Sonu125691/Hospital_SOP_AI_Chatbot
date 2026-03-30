import streamlit as st
import json
import re

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


st.title("Hospital SOP AI Chatbot")
st.markdown("This is a Hospital SOP AI Chatbot. There are a total of 8 departmental SOPs in this system." \
" You can simply ask questions related to this Hospital SOP.")


#----------getting json based data-----------------------------------------------------------------------------

with open("json_files.json", "r")as file:
    json_data = json.load(file)

#----------------------------------------------------------------------------------------------------------------


#----------getting RAG based data----------------------------------------------------------------------------

@st.cache_resource
def get_vectorstore():
    embedding = HuggingFaceEmbeddings(model_name = "sentence-transformers/all-MiniLM-L6-v2")
    vector_db = FAISS.load_local("faiss_index", embedding, allow_dangerous_deserialization = True)
    return vector_db

vectorstore = get_vectorstore()

#---------------------------------------------------------------------------------------------------------------


#-------------------------LLM------------------------------------------------------------------------------------

def llm(query, rule_context, rag_context):
    prompt = """
    You are an enterprise-grade Hospital SOP (Standard Operating Procedure) Assistant. 
    Your strict mandate is to extract and format information exclusively from the provided official hospital documents.

    The hospital has a total of 8 departments. The context provided to you will be formatted with metadata tags:
    - DEPARTMENT: The hospital unit the rule applies to.
    - SECTION: The category of the rule (e.g., Procedure, Responsibilities).
    - VALUE: The actual text of the SOP.

    You will receive two data sources:
    1. RULE BASED CONTEXT (Primary source)
    2. RAG BASED CONTEXT (Secondary fallback)

    STRICT INSTRUCTIONS:
    1. ADHERENCE: Answer ONLY using the provided context. Do not infer, assume, or generate outside medical information.
    2. PRIORITY: Always evaluate RULE BASED CONTEXT first. If the answer is found there, ignore RAG BASED CONTEXT entirely.
    3. REVERSE LOOKUPS: If the user asks which department or section a specific rule belongs to, look at the metadata tags.
    4. MULTIPLE INTENTS: If the user asks about multiple departments or procedures, extract and answer each one separately.
    5. MISSING DATA: If the exact answer is not found, reply: "The information is not available in the SOP."

    OUTPUT STYLE:
    - Answers must be clear, professional, and in natural language.
    - VERBATIM TECHNICALITY: While the language should be natural, all technical steps, codes, dates, and names must be extracted EXACTLY as they appear in the VALUE tag. 
    - Do not use conversational filler (e.g., "Based on the context...").
    
    RULE BASED CONTEXT:
    {rulec}

    RAG BASED CONTEXT:
    {ragc}

    QUESTION:
    {ques}
    """

    template = ChatPromptTemplate.from_template(prompt)

    llm_model = ChatGroq(
        api_key = st.secrets["GROQ_API_KEY"],
        model_name = "llama-3.3-70b-versatile", 
        temperature = 0.1
        )

    rag_chain = (
        template
        | llm_model
        | StrOutputParser()
    )

    answer = rag_chain.invoke({
        "rulec": rule_context,
        "ragc": rag_context,
        "ques": query
    })

    return answer

#------------------------------------------------------------------------------------------------------------------------------------


department_dictionary = {
    "blood_bank_operations": ["blood bank operations","blood bank", "blood bank operation"],
    "infection_control_protocol": [
        "infection control protocol", "infection control", "infection control protocols", "infection protocols",
        "infection protocol"],
    "biomedical_waste_management": ["biomedical waste management", "biomedical management"],
    "fire_safety_and_emergency_evacuation": [
        "fire safety and emergency evacuation", "fire safety", "fire and safety", "fire evacuation", "fire safety emergency evacuation",
        "fire emergency evacuation"],
    "icu_admission_and_triage": ["icu admission triage", "icu", "icu admission", "icu_admission",],
    "emergency_services_operations": [
        "emergency services operations", "emergency services", "emergency services operation", "emergency service",
        "emergency operations", "emergency service operations"],
    "operations_theatre_procedures": [
        "operations theatre procedures","operation theatre","operations theatre procedure"],
    "patient_discharge_process": ["patient discharge process", "patient discharge processes", "patient process", "patient processes"]
}

subheader_dictionary = {
    "overall_details_about_this_department": ["overall", "overview", "about", "details", "summary"],
    "title": ["title","name","sop name","procedure name","protocol name"],
    "sop_code_or_sop_id": ["sop code","code","sop id","procedure code","protocol code","sop number","sop no", "sop"],
    "version": ["version","sop version","current version","document version"],
    "effective_date": ["effective date","start date","valid from","implementation date","date effective"],
    "review_cycle_months": ["review cycle months","review","review cycle","review period","review time","review months","review interval","how often"],
    "department": ["department","which department","responsible department","handling department"],
    "approval_authority": ["approval authority","approved by","who approves","approval team","authorities","approval committee"],
    "documents_required": [
        "document required","documents", "document","required documents","forms","required forms","records",
        "documentation","what documents","what forms","paper"],
    "responsibilities": [
        "responsibility","responsibilities","roles","duties","who is responsible","who handles","staff responsibilities",
        "what do","role of","job of"],
    "purpose": ["purpose","purposes","objective","goal","aim"],
    "scope": ["scope","scopes","coverage","applicability"],
    "procedure": ["procedure","procedures","process","steps","workflow","how to","how do","how can"]
}


#-------------------------------------------------ANALYZE QUERY--------------------------------------------------------------------------------

def analyze_query(query):
    cleaned_query = query.lower()
    detect_department = False
    detect_section = False

    for dep_key, dep_values in department_dictionary.items():
        if any(values in cleaned_query for values in dep_values):
            detect_department = True

    for sub_key, sub_values in subheader_dictionary.items():
        if any(values in cleaned_query for values in sub_values):
            detect_section = True

    return {"detect_department": detect_department,
            "detect_section": detect_section}

#-----------------------------------------------------------------------------------------------------------------------------------------------


#--------------------------------------------RULE BASED RETRIVAL SYSTEM-----------------------------------------------------------------------------------------------------------------

def rule_based_retrieval_system(query):

    cleaned_query = query.lower()

    headings = {}

    # Detect Department
    for dep_key, dep_values in department_dictionary.items():
        if any(values in cleaned_query for values in dep_values):
            headings[dep_key] = []


    if not headings:
        return "NO CONTEXT IN THE RULE BASED SYSTEM"
    
    # Detect Sections
    else:
        for sub_key, sub_values in subheader_dictionary.items():
            if any(values in cleaned_query for values in sub_values):

                for head in headings:
                    headings[head].append(sub_key)
        
    # Adding Overall details about the department if it user query does not contains any Section then add overall content of the department
    if not any(headings.values()):
        for dep in headings:
            headings[dep].append("overall_details_about_this_department")

      
    # Extracting Context from Json data
    rule_based_dictionary = {}
    for head_key, head_values in headings.items():
        for value in head_values:
            if head_key not in rule_based_dictionary:
                rule_based_dictionary[head_key] = {value: json_data[head_key][value]}
            else:
                rule_based_dictionary[head_key].update({value: json_data[head_key][value]})

    
    # Cleaning the Extracted Context
    rule_based_cleaned_context = ""

    for key, values in rule_based_dictionary.items():
        for k, v in values.items():
            department = key.replace("_"," ")
            section = k.replace("_"," ")
            rule_based_cleaned_context += f"DEPARTMENT: {department}\nSECTION: {section}\nVALUE: \n{v}\n\n"

    return rule_based_cleaned_context

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#-------------------------------------------RAG BASED RETRIEVAL SYSTEM---------------------------------------------------------------------------------

#----------------Query Expansion----------------------------------
expansion_dict = {
    "document": "documents forms records documentation",
    "documents": "documents forms records documentation",
    "form": "forms documents records",
    "forms": "forms documents records",
    "procedure": "procedure steps process workflow",
    "procedures": "procedure steps process workflow",
    "responsibility": "responsibilities roles duties",
    "responsibilities": "responsibilities roles duties"
}

def query_expansion(query):
    words = re.findall(r"\w+", query)
    
    expanded_words = []

    for w in words:
        if w.lower() in expansion_dict:
            expanded_words.append(expansion_dict[w.lower()])
        else:
            expanded_words.append(w)

    return " ".join(expanded_words)

#------------------------------------------------------------------


#-------------Main Part------------------------------------------------------------------------------------------------------

def rag_based_retrieval_system(query, k_num):

    best_query = query_expansion(query)

    getting = vectorstore.similarity_search_with_score(best_query, k = k_num)
    rag_answer = [doc for doc, score in getting if score < 1.5]

    if not rag_answer:
        return "NO CONTEXT IN THE RAG BASED SYSTEM"
    
    #---------------Filtering rag answer-----------------------------------------------------------------------
    else:
        common_words = [
            "the", "is", "are", "was", "were",
            "what", "which", "who", "whom", "why", "how",
            "a", "an", "of", "to", "for", "in", "on", "at", "by", "with",
            "and", "or", "but", "if",
            "this", "that", "these", "those",
            "do", "does", "did",
            "can", "could", "should", "would",
            "will", "shall", "may", "might",
            "be", "been", "being",
            "as", "it", "its", "from"]
        
        # Cleaning User query by removing punctuations and common words
        query_words = re.findall(r"\w+", best_query.lower())
        cleaned_query_words = [word for word in query_words if word not in common_words]

        def rag_answer_sort(documents):
            h1 = documents.metadata.get("Header_1", "").lower()
            h2 = documents.metadata.get("Header_2", "").lower()
            h3 = documents.metadata.get("Header_3", "").lower()
            content = documents.page_content.lower()
            combined = f"{h1} {h2} {h3} {content}"

            # Rag document by removign punctuations and common words
            document_words = re.findall(r"\w+", combined.lower())
            cleaned_document_words = [word for word in document_words if word not in common_words]

            return sum(word in cleaned_document_words for word in cleaned_query_words)
        
        filtered_rag_answer = sorted(rag_answer, key = rag_answer_sort, reverse = True)

    #---------------------------------------------------------------------------------------------------------------------------


    #-------------------------Rag Answer Final Cleaning-------------------------------------------------------------

    cleaned_answer = ""
    for doc in filtered_rag_answer:
        h1 = doc.metadata.get("Header_1","")
        h2 = doc.metadata.get("Header_2","")
        h3 = doc.metadata.get("Header_3","")
        content = doc.page_content

        cleaned_answer += f"DEPARTMENT: {h1}\nSECTION: {h2} > {h3}\nVALUE: \n{content}\n\n"

    return cleaned_answer

    #-----------------------------------------------------------------------------------------------------------------------


#---------------Showing Previous chats----------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

#-------------------------------------------------------------------------------------------------


#-------------------------------FINAL PART: RULE CONTEXT + RAG CONTEXT + LLM--------------------------------------------------------------------------------------------------

user_query = st.chat_input("Type Here.....")

if user_query:
    with st.chat_message("user"):
        st.markdown(user_query)

    analyze_query_answer = analyze_query(user_query)


    #-----IF USER QUERY HAS NO DEPARTMENT AND SECTION---------------------------------------------------------
    if analyze_query_answer["detect_department"] == False and analyze_query_answer["detect_section"] == False:
        final_output = "Please ask questions related to Hospital SOP (e.g., department, procedure, responsibilities)."


    #-----IF USER QUERY HAS DEPARTMENT BUT NO SECTION---------------------------------------------------------
    elif analyze_query_answer["detect_department"] == True and analyze_query_answer["detect_section"] == False:

        #------IF USER QUERY CONTAINS MULTIPLE INTENT----------------------------
        multiple_intent = [" and ",","]
        user_query_cleaned = user_query.lower()
        if any(words in user_query_cleaned for words in multiple_intent):
            rule_based_answer = rule_based_retrieval_system(user_query)
            rag_based_answer = rag_based_retrieval_system(user_query, 5)

            final_output = llm(user_query, rule_based_answer, rag_based_answer)  

        #-----IF USER QUERY CONTAINS NO MULTIPLE INTENT--------------------------
        else:
            rule_based_answer = rule_based_retrieval_system(user_query)
            rag_based_answer = "NO CONTEXT IN THE RAG BASED SYSTEM"

            final_output = llm(user_query, rule_based_answer, rag_based_answer)
         

    #-----IF USER QUERY CONTAINS NO DEPARTMENT BUT HAS SECTION------------------------------------------------------------
    elif analyze_query_answer["detect_department"] == False and analyze_query_answer["detect_section"] == True:

        user_query_cleaned = " " + user_query.lower() + " "
        broad_words = [" all ", " all.", "everything", "full details"]

        #-------IF USER QUERY CONTAINS THE WORD "WHICH"----------------
        if "which" in user_query_cleaned:
            rule_based_answer = "NO CONTEXT IN THE RULE BASED SYSTEM"
            rag_based_answer = rag_based_retrieval_system(user_query, 5)

            final_output = llm(user_query, rule_based_answer, rag_based_answer)

        #-----IF USER QUERY CONTAINS BROAD WORDS---------------------
        elif any(words in user_query_cleaned for words in broad_words):
            final_output = "Please specify about department or section"
            
        else:
            final_output = "Please clarify your question"


    #------IF USER QUERY HAS DEPARTMENT AND SECTION------------------------------------------------------------
    else:
        rule_based_answer = rule_based_retrieval_system(user_query)
        rag_based_answer = rag_based_retrieval_system(user_query, 5)

        final_output = llm(user_query, rule_based_answer, rag_based_answer)  


    with st.chat_message("assistant"):
        st.markdown(final_output)

    st.session_state.messages.append({"role": "user", "content": user_query})
    st.session_state.messages.append({"role": "assistant", "content": final_output})