import { MCPFunction, MCPFunctionGroup } from "@modelcontextprotocol/sdk";
import { Translate } from "@google-cloud/translate/build/src/v2";

// Utility function for safe execution with error handling
function safelyExecute<T>(fn: () => Promise<T>): Promise<T> {
  return fn().catch(error => {
    throw new Error(`Operation failed: ${error instanceof Error ? error.message : String(error)}`);
  });
}

interface VideoTranslation {
  [language: string]: {
    title?: string;
    description?: string;
    tags?: string[];
    [key: string]: any;
  };
}

interface LanguageDetection {
  language: string;
  confidence: number;
}

interface LanguageSegment extends LanguageDetection {
  text: string;
}

export class TranslationManager implements MCPFunctionGroup {
  private youtube: any;
  private translate: Translate;

  constructor() {
    this.youtube = google.youtube({
      version: "v3",
      auth: process.env.YOUTUBE_API_KEY
    });
    this.translate = new Translate({
      projectId: process.env.GOOGLE_PROJECT_ID,
      key: process.env.GOOGLE_TRANSLATE_API_KEY
    });
  }

  @MCPFunction({
    description: "Translate video captions to multiple languages",
    parameters: {
      type: "object",
      properties: {
        videoId: { type: "string" },
        targetLanguages: { 
          type: "array", 
          items: { type: "string" }
        }
      },
      required: ["videoId", "targetLanguages"]
    }
  })
  async translateCaptions({ 
    videoId, 
    targetLanguages 
  }: {
    videoId: string;
    targetLanguages: string[];
  }): Promise<Record<string, string[]>> {
    return safelyExecute(async () => {
      const captions = await this.youtube.captions.list({
        part: ["snippet"],
        videoId
      });

      if (!captions.data.items?.length) {
        throw new Error(`No captions found for video: ${videoId}`);
      }

      const results: Record<string, string[]> = {};

      for (const caption of captions.data.items) {
        const track = await this.youtube.captions.download({
          id: caption.id
        });

        for (const lang of targetLanguages) {
          const [translation] = await this.translate.translate(track.data, lang);
          if (!results[lang]) {
            results[lang] = [];
          }
          results[lang].push(translation);
        }
      }

      return results;
    });
  }

  @MCPFunction({
    description: "Translate video metadata to multiple languages",
    parameters: {
      type: "object",
      properties: {
        videoId: { type: "string" },
        targetLanguages: { 
          type: "array", 
          items: { type: "string" }
        },
        fields: { 
          type: "array", 
          items: { 
            type: "string",
            enum: ["title", "description", "tags"]
          }
        }
      },
      required: ["videoId", "targetLanguages"]
    }
  })
  async translateMetadata({ 
    videoId, 
    targetLanguages,
    fields = ["title", "description", "tags"]
  }: {
    videoId: string;
    targetLanguages: string[];
    fields?: string[];
  }): Promise<VideoTranslation> {
    return safelyExecute(async () => {
      const video = await this.youtube.videos.list({
        part: ["snippet"],
        id: [videoId]
      });

      if (!video.data.items?.length) {
        throw new Error(`Video not found: ${videoId}`);
      }

      const translations: VideoTranslation = {};

      for (const lang of targetLanguages) {
        translations[lang] = {};
        const snippet = video.data.items[0].snippet;

        for (const field of fields) {
          if (field === "tags" && snippet.tags) {
            const [translatedTags] = await this.translate.translate(
              snippet.tags,
              lang
            );
            translations[lang].tags = Array.isArray(translatedTags) 
              ? translatedTags 
              : [translatedTags];
          } else {
            const content = snippet[field];
            if (content) {
              const [translation] = await this.translate.translate(content, lang);
              translations[lang][field] = translation;
            }
          }
        }
      }

      return translations;
    });
  }

  @MCPFunction({
    description: "Detect spoken languages in video",
    parameters: {
      type: "object",
      properties: {
        videoId: { type: "string" },
        segments: { 
          type: "boolean",
          description: "Whether to detect languages in segments"
        }
      },
      required: ["videoId"]
    }
  })
  async detectLanguages({ 
    videoId, 
    segments = false 
  }: {
    videoId: string;
    segments?: boolean;
  }): Promise<LanguageDetection | LanguageSegment[]> {
    return safelyExecute(async () => {
      const captions = await this.youtube.captions.list({
        part: ["snippet"],
        videoId
      });

      if (!captions.data.items?.length) {
        throw new Error(`No captions found for video: ${videoId}`);
      }

      if (segments) {
        return this.detectLanguageSegments(captions.data.items);
      }

      const allText = await this.getAllCaptionText(captions.data.items);
      const [detection] = await this.translate.detect(allText);
      
      return {
        language: detection.language,
        confidence: detection.confidence
      };
    });
  }

  private async detectLanguageSegments(captions: any[]): Promise<LanguageSegment[]> {
    const segments: LanguageSegment[] = [];
    const segmentSize = 1000; // Characters per segment

    for (const caption of captions) {
      const track = await this.youtube.captions.download({
        id: caption.id
      });

      let currentSegment = "";
      const words = track.data.split(/\s+/);

      for (const word of words) {
        currentSegment += word + " ";
        if (currentSegment.length >= segmentSize) {
          const [detection] = await this.translate.detect(currentSegment);
          segments.push({
            text: currentSegment.trim(),
            language: detection.language,
            confidence: detection.confidence
          });
          currentSegment = "";
        }
      }

      if (currentSegment) {
        const [detection] = await this.translate.detect(currentSegment);
        segments.push({
          text: currentSegment.trim(),
          language: detection.language,
          confidence: detection.confidence
        });
      }
    }

    return this.mergeConsecutiveSegments(segments);
  }

  private async getAllCaptionText(captions: any[]): Promise<string> {
    const texts = await Promise.all(
      captions.map(async caption => {
        const track = await this.youtube.captions.download({
          id: caption.id
        });
        return track.data;
      })
    );
    
    return texts.join(" ").trim();
  }

  private mergeConsecutiveSegments(segments: LanguageSegment[]): LanguageSegment[] {
    const merged: LanguageSegment[] = [];
    let current: LanguageSegment & { confidence: number[] } | null = null;

    for (const segment of segments) {
      if (!current || current.language !== segment.language) {
        if (current) {
          merged.push({
            ...current,
            confidence: current.confidence.reduce((a, b) => a + b) / current.confidence.length
          });
        }
        current = {
          ...segment,
          confidence: [segment.confidence]
        };
      } else {
        current.text += " " + segment.text;
        current.confidence.push(segment.confidence);
      }
    }

    if (current) {
      merged.push({
        ...current,
        confidence: current.confidence.reduce((a, b) => a + b) / current.confidence.length
      });
    }

    return merged;
  }
}