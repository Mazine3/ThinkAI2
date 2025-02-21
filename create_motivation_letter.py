from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import re, os

MODEL_NAME = "deepseek-r1-distill-llama-70b"
GROQ_API_KEY=os.getenv('GROQ_API_KEY', '')

def get_llm_response(context, email, name, adresse, phone, date, langue):
    llm = ChatGroq(
        api_key= GROQ_API_KEY,
        model=MODEL_NAME,
        temperature=0
        )
    
    prompt_template = ChatPromptTemplate.from_template(
        f"""
        You are an expert in creating letters of motivation for job applications.
        I will provide you with a job description in the context, and you will generate a professional letter of motivation for this job.
        Do not include any system words or thinking sentences just provide the letter of motivation without anything else and do not put things to completed the version that you will give it to me i will send it directly:
        i want the output of the lettre of motivation to be with language : {langue}


        my name is : {name}
        my email is : {email}
        my phone is : {phone}
        my adresse is : {adresse}
        date of today is : {date}

        
        <job_description>
        Job description: {context}
        </job_description>
        """
        )
    
    prompt = prompt_template.format()
    response = llm.invoke(prompt)
    answer = response.content
    answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL)
    answer = re.sub(r"\*\*.*?\*\*", "", answer)
    return answer