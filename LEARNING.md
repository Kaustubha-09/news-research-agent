# What We Built (in plain language)

This is a research assistant. You type in a topic, and it:
1. Searches the internet for current information
2. Decides for itself whether it found enough good information (and searches again if not)
3. Writes a clean summary with a headline, bullet points, and sources
4. Generates a picture to go with it
5. Shows all of that on a webpage

The interesting part isn't the search or the writing — it's that the program **makes its own decisions** about what to do next. That's what "AI agent" means: not just "ask a question, get an answer," but "give it a goal, and it figures out the steps."

## The building blocks, explained without jargon

**The LLM (Groq)**
This is the actual "brain" — a large language model that reads text and generates text back. Think of it as a very well-read assistant you can ask questions to. We used Groq because it's fast and has a free tier to start with.

**Tool calling**
The LLM by itself can only make things up from what it already knows — it doesn't automatically know today's news. So we gave it a "tool": a web search function. The LLM can say "I need to search for X," but it can't actually do the search itself — our code does the search and hands the results back to it. It's like an assistant who can ask a librarian to fetch a book, but can't walk to the shelf themselves.

**LangGraph (the orchestration part)**
This is the part that manages *the steps* the agent takes: search, then decide if that's enough, then either search again or write the summary, then make the picture. Think of it as a flowchart that the program actually follows, where some steps can loop back if needed. This is the difference between a simple script (does A, then B, then C, always the same) and an *agent* (does A, then decides whether to do A again or move to B).

**"Reflection" / the search-enough-yet check**
After searching, we have the LLM look at what it found and literally judge itself: "is this enough information, or should I search again?" This mimics how a person would research something — you don't stop after the first Google result if it wasn't useful. We also set a hard limit (max 3 searches) so it can't get stuck looping forever and wasting time/money if it's never satisfied.

**Structured output**
Normally an LLM just replies with a paragraph of text. We forced it to reply in a specific, predictable shape instead — always a headline, always a list of bullet points, always a list of sources. This matters because a website or app needs predictable data to display, not a paragraph it has to guess how to parse.

**Image generation**
Once we have the written report, we ask a *different* AI model — one that makes pictures — to generate a cover image based on a short description. We learned along the way that these image models are bad at drawing legible text, so we told it to only describe visual scenes, no words or labels.

**The web server (FastAPI)**
This is what turns our Python program into something a website can actually talk to. Without it, our agent would only work if you ran it directly on your own computer from the command line. With it, any webpage (or app, or another program) can send it a topic and get back a report over the internet.

**The website (React)**
This is the part you actually see and click on — a text box to type your topic, a button, and a display area for the results. It talks to the FastAPI server behind the scenes whenever you hit "Research."

**Docker (containers)**
Normally, "it works on my computer" doesn't guarantee it'll work anywhere else — different computers have different setups. Docker packages the program *and* everything it needs to run into one self-contained box (a "container") that behaves identically no matter where you run it — your laptop, a cloud server, anywhere.

**Azure (the cloud deployment)**
This is where we actually put the program so it runs on the internet permanently, instead of only working while your laptop is on and a terminal window is open. A few different Azure services work together:
- **Container Registry**: stores our packaged program (the Docker container)
- **Container Apps**: actually runs the program, 24/7, and gives it a public web address
- **Blob Storage**: stores the generated pictures so they don't disappear when the program restarts
- **Static Web Apps**: hosts the website part (React) separately, since it doesn't need the same kind of "always running" server the backend does

## The debugging stories worth remembering

These weren't failures — they're exactly the kind of real-world problem-solving that's hard to learn from a tutorial:

- **The image came out with garbled text.** Turns out AI image generators are bad at spelling — so we stopped asking for text in the picture and let the real headline/bullets be regular website text instead.
- **It worked on my laptop but crashed in the cloud.** My laptop is a different kind of computer chip (Apple Silicon) than what Azure uses, so the packaged program had to be rebuilt specifically for Azure's chip type.
- **The cloud version couldn't remember its login key.** A tiny formatting mistake (leftover quotation marks) in the secret key file caused it to send a broken key. Fixed by cleaning up how we read that value.
- **Updating the program on Azure didn't do anything.** Azure assumed nothing had changed because we kept reusing the same "version label" for the update. Once we started labeling each update with a new version number, it started working reliably — this is actually standard practice in real software teams, not just a workaround.

## The one-sentence version for a resume or interview

"I built an AI agent that researches topics on the web, decides for itself when it has enough information, writes a structured report with an image, and deployed the whole thing — website, server, and storage — to the cloud."
