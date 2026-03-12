declare namespace google {
  namespace cloud {
    class LanguageServiceClient {
      constructor();
      analyzeSentiment(request: any): Promise<any>;
    }

    class SpeechClient {
      constructor();
      longRunningRecognize(request: any): Promise<any>;
    }

    class TranslateClient {
      constructor();
      translate(text: string, target: string): Promise<any>;
    }
  }
}

declare namespace canvas {
  function createCanvas(width: number, height: number): any;
  function loadImage(src: string): Promise<any>;
}