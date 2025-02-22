from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import re, os

MODEL_NAME = "deepseek-r1-distill-llama-70b"
GROQ_API_KEY=os.getenv('GROQ_API_KEY', '')

def get_llm_response(jobtitle, name, company_name, writer_to, skills, role_type, job_location, today_date, jb_offre, langue="English"):
    llm = ChatGroq(
        api_key= GROQ_API_KEY,
        model=MODEL_NAME,
        temperature=0
        )
    
    prompt_template = ChatPromptTemplate.from_template(
        f"""
            You are an expert in creating letters of motivation for job applications.
            don't give me or display incompleted things like '[Your Phone Number]"ect.., and the output i want it to be with good format to put it directly in the pdf file.
            I will provide you with the following details:

            Job title : {jobtitle}
            My name : {name}
            Company name : {company_name}
            The recipient of the letter : {writer_to}
            My skills : {skills}
            My role type : {role_type}
            Adresse : {job_location}
            Date : {today_date}

            offre description : {jb_offre}

            Using this information, please generate a professional letter of motivation for the specified job. Do not include any system instructions or thought processes—only the final letter itself. It should be ready to send immediately, without any additional placeholders or edits. The language of the letter should be: {langue}.
        """
        )
    
    prompt = prompt_template.format()
    response = llm.invoke(prompt)
    answer = response.content
    answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL)
    answer = re.sub(r"\*\*.*?\*\*", "", answer)
    return answer
