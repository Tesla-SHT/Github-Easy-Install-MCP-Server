# GitHub Easy Install MCP Server

Have you ever been haunted by the environment configuration of AI model for several days? Have you ever been lost by the overwhelming red ERRORs full of the screen? Have you ever been bored with toggling between asking LLM and typing the modified commands?

Our innovative NLP project (Star and Play) uses Model Context Protocol (MCP) to automate GitHub repository installations. The system features two components: a GitHub MCP server that analyzes repositories and generates installation commands, and a Local CLI MCP server that executes these commands while providing intelligent error handling through LLM integration. This solution streamlines the typically complex repository installation process into a seamless experience.

# MCP-Introduction

**MCP (Model Context Protocol)** is an open protocol standard in the large language model (LLM) domain introduced by Anthropic. It aims to address the integration challenges between LLMs and external data sources, tools, or services through standardized interaction mechanisms. Simply put, MCP enables LLM-based chat systems to use diverse tools in a more standardized way.

When a user asks a question:

1. The client (e.g., **Claude Desktop** or **Cursor**) sends your question to the LLM (e.g., **Claude**).
2. **Via prompt engineering**, the LLM analyzes available tools and decides which one (or multiple) to use.
3. The selected tool is executed through the **MCP Server**.
4. The execution result from the tool is sent back to the LLM.
5. The LLM combines the execution result to construct the final prompt and generates a natural language response.
6. The response is ultimately presented to the user.

# Procedure

Our project mainly consists of two components: GitHub Server and Local CLI Server. The user can use the Cline, which is the extensions of VSCode, or use Claude Desktop as the **client**. And the LLM will call our servers in series.

When doing the tasks, we have a standard first try, if it succeeds, then it’s done. If it fails, we turn to LLM for correcting, if it succeeds, then it’s done. If it fails, then we turn to related society to provide more information to LLM, and if it still can not correct the error, then the task fails.

## GitHub Server

1. Input the repository URL
2. Identify critical files (README.md, requirements.txt, environment.yml) via git ingest
3. LLM will get the data from the server through MCP and generate the executable file
    
    ### Existing Method:
    
    The server of fetching information from GitHub repository like the structure or basic info already exists.
    
    ### Improvement:
    
    we want to improve its accuracy and efficiency specifically for installation and generate regularized commands. 
    

## Local CLI Server

1. LLM will call the CLI server to run the script file or commands
2. The server will also collect the system output like error or success of the installation, and we plan to use NLP relative model to locally analyze the content →to reduce the interacting time with LLM and also reduce the token consumption.
3. The organized information will be transmitted to LLM and the modified commands will be fed into the Local CLI Server again
    
    ### Existing Method:
    
    The server that runt he script file or commands already exists
    
    ### Improvement:
    
    We will try to put emphasis on developing the analyzing model of the system output. And the error correction mechanism should be an innovation for the MCP server.
    

## Optional Further Application

1. We can collect the error during installation to let LLM generate a better readme/requirements/environment files.
2. Generate detailed issues automatically if our server finds error from the original guideline.

# Challenges

1. We are not familiar enough to the mechanism of MCP
2. Some commands may depend on the user’s own computer system, like the operating system, file or system path, etc. So we may need to let the LLM ask relative information automatically.
3. We may need to design or utilize some tools to avoid frequent interactions with LLM due to the token limit, since the token and context limit will stop the process halfway
4. Hardware-specific dependencies (e.g., GPU acceleration libraries like CUDA) may cause installation failures, requiring hardware configuration detection, and send the information to LLM.
5. If Errors can be caused by different reasons, the LLM may return them together, we may need some prompt engineering to divide the different command in this case to try each possible solution.
6. It’s necessary to set a security check system so it will not cause some security problems.

# Evaluation and Test

Evaluation dataset and test dataset will be some of ‘readme.md’, ‘requirements.txt’ files available on GitHub. This dataset should contain both well written and badly written examples for better tests. 

Evaluate on the succeed rate of every steps of our procedure and check common errors and decides for further improvements.

# Link

https://github.com/adhikasp/mcp-git-ingest

https://github.com/g0t4/mcp-server-commands

https://mcpcn.com/docs/

[Introduction - Model Context Protocol](https://modelcontextprotocol.io/introduction)
