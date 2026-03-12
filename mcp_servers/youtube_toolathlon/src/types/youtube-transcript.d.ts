declare module 'youtube-transcript' {
  export interface TranscriptLine {
    text: string;
    offset: number;
    duration: number;
  }

  export class YoutubeTranscript {
    static fetchTranscript(videoId: string): Promise<TranscriptLine[]>;
  }

  export default YoutubeTranscript;
}