|page_type| languages                               |products
|---|-----------------------------------------|---|
|sample| <table><tr><td>Python</tr></td></table> |<table><tr><td>azure</td><td>azure-communication-services</td></tr></table>|

# Call Automation - Quick Start Sample

This is a sample application demonstrated during Microsoft Build 2023. It highlights an integration of Azure Communication Services with Azure OpenAI Service to enable intelligent conversational agents.

## Prerequisites

- Create an Azure account with an active subscription. For details, see [Create an account for free](https://azure.microsoft.com/free/)
- Create an Azure Communication Services resource. For details, see [Create an Azure Communication Resource](https://docs.microsoft.com/azure/communication-services/quickstarts/create-communication-resource). You'll need to record your resource **connection string** for this sample.
- An Calling-enabled telephone number. [Get a phone number](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/telephony/get-phone-number?tabs=windows&pivots=platform-azp).
- Azure Dev Tunnels CLI. For details, see  [Enable dev tunnel](https://docs.tunnels.api.visualstudio.com/cli)
- Create an Azure Cognitive Services resource. For details, see [Create an Azure Cognitive Services Resource](https://learn.microsoft.com/en-us/azure/cognitive-services/cognitive-services-apis-create-account)
- An Azure OpenAI Resource and Deployed Model. See [instructions](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal).
- Create and host a Azure Dev Tunnel. Instructions [here](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started)
- [Python](https://www.python.org/downloads/) 3.7 or above.

## Before running the sample for the first time

1. Open an instance of PowerShell, Windows Terminal, Command Prompt or equivalent and navigate to the directory that you would like to clone the sample to.
2. git clone `https://github.com/Azure-Samples/communication-services-python-quickstarts.git`.
3. Navigate to `callautomation-openai-sample` folder and open `main.py` file.

### Setup the Python environment

Create and activate python virtual environment and install required packages using following command 
```
pip install -r requirements.txt
```

### Setup and host your Azure DevTunnel

[Azure DevTunnels](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/overview) is an Azure service that enables you to share local web services hosted on the internet. Use the commands below to connect your local development environment to the public internet. This creates a tunnel with a persistent endpoint URL and which allows anonymous access. We will then use this endpoint to notify your application of calling events from the ACS Call Automation service.

```bash
devtunnel create --allow-anonymous
devtunnel port create -p 8080
devtunnel host
```

### Configuring application

Open `main.py` file to configure the following settings

1. - `CALLBACK_URI_HOST`: your dev tunnel endpoint
2. - `COGNITIVE_SERVICE_ENDPOINT`: The Cognitive Services endpoint
3. - `ACS_CONNECTION_STRING`: Azure Communication Service resource's connection string.
4. - `AZURE_OPENAI_SERVICE_KEY`: Open AI's Service Key
5. - `AZURE_OPENAI_SERVICE_ENDPOINT`: Open AI's Service Endpoint
6. - `AZURE_OPENAI_DEPLOYMENT_MODEL_NAME`: Open AI's Model name
6. - `AGENT_PHONE_NUMBER`: Agent Phone Number to transfer call

## Run app locally

1. Navigate to `callautomation-openai-sample` folder and run `main.py` in debug mode or use command `python ./main.py` to run it from PowerShell, Command Prompt or Unix Terminal
2. Browser should pop up with the below page. If not navigate it to `http://localhost:8080/` or your dev tunnel url.
3. Register an EventGrid Webhook for the IncomingCall Event that points to your DevTunnel URI. Instructions [here](https://learn.microsoft.com/en-us/azure/communication-services/concepts/call-automation/incoming-call-notification).

Once that's completed you should have a running application. The best way to test this is to place a call to your ACS phone number and talk to your intelligent agent.
