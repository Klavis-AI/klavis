declare module 'ytdl-core' {
  import { Readable } from 'stream';

  interface YtdlOptions {
    quality?: string;
  }

  function ytdl(url: string, options?: YtdlOptions): Readable;
  
  namespace ytdl {
    export interface VideoInfo {
      videoDetails: {
        title: string;
        // Add other properties as needed
      };
    }
    
    export function getInfo(url: string): Promise<VideoInfo>;
  }

  export = ytdl;
}