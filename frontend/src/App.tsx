import React, { useState } from "react";
import axios from "axios";
import { Graphviz } from "graphviz-react";

interface Function {
  name: string;
  line_number: number;
  end_line_number: number;
}

interface Method extends Function {}

interface Class {
  name: string;
  line_number: number;
  end_line_number: number;
  methods: Method[];
}

interface Module {
  filename: string;
  classes: Class[];
  functions: Function[];
}

const App: React.FC = () => {
  const [path, setPath] = useState<string>("");
  const [dotString, setDotString] = useState<string>("");
  const [error, setError] = useState<string>("");

  console.log("dotString", dotString);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setDotString("");

    try {
      const response = await axios.post<Module[]>(
        "http://localhost:8000/visualize",
        { path }
      );
      const data = response.data;

      // Generate DOT string,
      let dot = "digraph G {\n";
      dot += "  rankdir=TB;\n"; // Top to Bottom direction
      dot += "  node [shape=box];\n";

      data.forEach((file, fileIndex) => {
        const fileName = file.filename.split("/").pop() || "";
        dot += `  subgraph cluster_${fileIndex} {\n`;
        dot += `    label="${fileName}";\n`;
        dot += `    URL="cursor://file${file.filename}";\n`;
        dot += `    color=blue;\n`;

        file.classes.forEach((cls, clsIndex) => {
          dot += `    subgraph cluster_${fileIndex}_${clsIndex} {\n`;
          dot += `      label="${cls.name}";\n`;
          dot += `      URL="cursor://file${file.filename}:${cls.line_number}";\n`;
          dot += `      color=red;\n`;

          cls.methods.forEach((method, methodIndex) => {
            dot += `      method_${fileIndex}_${clsIndex}_${methodIndex} [label="${method.name}", URL="cursor://file${file.filename}:${method.line_number}"];\n`;
          });

          dot += "    }\n";
        });

        file.functions.forEach((func, funcIndex) => {
          dot += `    func_${fileIndex}_${funcIndex} [label="${func.name}", URL="cursor://file${file.filename}:${func.line_number}"];\n`;
        });

        dot += "  }\n";
      });
      dot += "}";

      setDotString(dot);
    } catch (err) {
      setError("Error fetching data. Please check the path and try again.");
      console.error(err);
    }
  };

  const handleNodeClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement;
    const url = target.getAttribute("href");
    if (url) {
      event.preventDefault();
      window.open(url, "_blank");
    }
  };

  return (
    <div className="container mx-auto p-4 flex flex-col h-screen">
      <h1 className="text-2xl font-bold mb-4">Repository Viewer</h1>
      <form onSubmit={handleSubmit} className="mb-4" autoComplete="on">
        <label htmlFor="path" className="mr-2">
          Repository Path:
        </label>
        <input
          type="text"
          name="path"
          value={path}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setPath(e.target.value)
          }
          placeholder="Enter repository path"
          className="border p-2 mr-2"
        />
        <button type="submit" className="bg-blue-500 text-white p-2 rounded">
          Visualize
        </button>
      </form>
      {error && <p className="text-red-500 mb-4">{error}</p>}
      {dotString && (
        <div className="border p-4 flex-1" onClick={handleNodeClick}>
          <Graphviz
            className="h-full w-full"
            dot={dotString}
            options={{ width: "100%", height: "100%", zoom: true }}
          />
        </div>
      )}
    </div>
  );
};

export default App;
