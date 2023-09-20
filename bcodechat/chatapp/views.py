from django.shortcuts import render, redirect
from .forms import UserForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from datetime import datetime
from .models import QuestionAnswer
import os
from dotenv import load_dotenv
import openai 
from PyPDF2 import PdfReader
import json
import pickle
import torch
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain




# Create your views here.


# create three main views

load_dotenv()



@login_required(login_url='signin')
def index(request):
    context = {}
    return render(request, "chatapp/index.html", context)

def signup(request):
    if request.user.is_authenticated:
        return redirect("index")
    form = UserForm()
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            username = request.POST["username"]
            password = request.POST["password1"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("index")

    context = {"form": form}
    return render(request, "chatapp/signup.html", context)


def signin(request):
    err = ""  # Define err here to ensure it always has a value
    if request.user.is_authenticated:
        return redirect("index")
    
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("index")
        else:
            err = "Invalid Credentials"
    
    context = {"error": err}
    return render(request, "chatapp/signin.html", context)


def signout(request):
    logout(request)

    return redirect("signin")


import os
import pickle
import json
from django.http import JsonResponse
from PyPDF2 import PdfReader  # Ensure to install this package
# Import other necessary modules here

# Initialize necessary variables and objects here
pdf_path = "OBC.pdf"
store_name = "faiss_OBC"

def ask_openai(message):
    try:
        # Load the PDF and extract text
        with open(pdf_path, "rb") as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()

        # Split the text and embed it
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
        chunks = text_splitter.split_text(text=text)

        # Load or create the vector store
        if os.path.exists(f"{store_name}.pk1"):
            with open(f"{store_name}.pk1", "rb") as f:
                VectorStore = pickle.load(f)
        else:
            embeddings = OpenAIEmbeddings()
            VectorStore = FAISS.from_texts(chunks, embedding=embeddings)
            with open(f"{store_name}.pk1", "wb") as f:
                pickle.dump(VectorStore, f)

        # Perform similarity search
        docs = VectorStore.similarity_search(query=message)

        # Get the response using your QA chain (adjust as necessary)
        llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0., streaming=True)
        chain = load_qa_chain(llm=llm, chain_type="stuff")
        response = chain.run(input_documents=docs, question=message)
    except Exception as e:
        response = str(e)  # Return the exception message as the response in case of an error
    #print(response)
    return response

def getValue(request):
    data = json.loads(request.body)
    message = data["msg"]
  
    answer = ask_openai(message)
    QuestionAnswer.objects.create(user=request.user, question=message, answer=answer)
    print(answer)
    return JsonResponse({"msg": message, "response": answer}, safe=False)

#def getValue(request):
#    data = json.loads(request.body)
#    message = data["msg"]
  
#    answer = ask_openai(message)






#    return JsonResponse({"response": answer}, safe=False)  # Returning the answer in JSON response
    #return JsonResponse({"response": response}, safe=False)

