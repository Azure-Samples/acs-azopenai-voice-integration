param aiServAccName string = 'ai-speech-${uniqueString(resourceGroup().id)}'

module aiServAccModule 'br/public:avm/res/cognitive-services/account:0.8.0' = {
  name: 'aiSpeechDeployment'
  params: {
    kind: 'SpeechServices'
    name: aiServAccName
  }
}
