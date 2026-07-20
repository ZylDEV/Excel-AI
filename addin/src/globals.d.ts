import "react";

declare global {
  namespace JSX {
    interface IntrinsicElements {
      [elemName: string]: any;
    }
  }
  
  const Excel: any;
  namespace Excel {
    interface RunOptions {}
    function run(callback: (context: any) => Promise<void>, options?: RunOptions): Promise<void>;
  }
}

export {};
