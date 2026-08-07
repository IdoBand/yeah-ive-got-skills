---
name: create-mermaid-diagrams
description: When the user wants a workflow, pipeline, architecture, sequence, class model, or state machine drawn as a diagram instead of described in prose — e.g. "diagram this", "visualize the flow", "draw the architecture", "show me a sequence diagram", or any back-and-forth design discussion that is hard to follow as terminal text. Writes Mermaid into a markdown file the user previews in their editor.
---

## 1. File choice — default to `.md`, not `.mmd`

| Form | Contents | Renders in VS 2026 |
|---|---|---|
| `.md` with ` ```mermaid ` fences | prose + any number of diagrams in one document | **Yes — built in** |
| `.mmd` | one diagram, no prose | No — needs a marketplace extension |

Write a `.md` unless the user explicitly asks for `.mmd`. The built-in Visual Studio
renderer is the *Markdown* preview, so `.mmd` gets no rendering out of the box, and
splitting a design into one-diagram files loses the argument that surrounds them.

Put the file where it belongs to the project, not to a personal account: `docs/design/<topic>.md`,
or beside the code it describes. Committed markdown is PR-reviewable, versioned with
the code, and readable by teammates with no setup.

## 2. Viewing — state this to the user, don't assume

| Environment | Setup | How to open |
|---|---|---|
| **Visual Studio 2026** | none | open the `.md`, click **Split Preview** (live, side by side) or **Open Preview** (rendered only). Zoom controls sit top-left of the preview pane |
| Visual Studio 2022 | not supported | Mermaid rendering is a 2026 feature |
| VS Code | **extension required** — `code --install-extension bierner.markdown-mermaid` | `Ctrl+Shift+V` |
| GitHub | none | renders natively in the web view once pushed |

Split Preview updates as the file changes on disk — that is the loop: edit the file,
the user reacts to the picture, repeat. Never build a `.sln` to hold diagram files;
a solution containing only a solution folder fails to load in VS 2026.

## 3. Pick the diagram type from the question being asked

| Question | Type |
|---|---|
| What are the pieces and what talks to what? | `flowchart TB` (or `LR` for wide monitors) |
| What happens, in what order, across components? | `sequenceDiagram` |
| What are the types and how do they relate? | `classDiagram` |
| What states can this thing be in, and who moves it? | `stateDiagram-v2` |
| What is the schedule? | `gantt` |

## 4. Colour must encode something

Never colour decoratively. Pick one axis and hold it across every diagram in the
document — where code runs, trust boundary, built vs proposed, durable vs losable —
and state the key in a line of prose under or above the diagrams.

```
classDef desktop  fill:#DCE9F5,stroke:#2D6A9F,stroke-width:1.5px,color:#14344E
classDef backend  fill:#DDEBE0,stroke:#3F7A54,stroke-width:1.5px,color:#1D3B26
classDef external fill:#F6E9D2,stroke:#B0752A,stroke-width:1.5px,color:#4A3110
classDef proposed stroke-dasharray: 5 4

class ui,runner desktop
class api,merge backend
class merge proposed        %% classes compose — merge is backend AND dashed
```

- Always pair a light `fill:` with an explicit dark `color:` so text stays legible in
  both light and dark preview panes.
- `classDef` + `class a,b name` — rock solid in `flowchart`. In `classDiagram` apply
  with `class Foo:::name`; in `stateDiagram-v2` with `class Foo name`. Both need a
  recent Mermaid — if only those two fail to render, that is why.
- `sequenceDiagram`: shade a span of steps with `rect rgb(246,233,210) … end` to mark
  a failure region or transaction boundary.

## 5. Rules

1. Quote every node label — `ui["Redline window · WPF"]`. Unquoted parentheses and
   slashes are parse errors.
2. No `<br/>` inside a diagram embedded in HTML — it is consumed as markup and the
   label breaks. Rephrase the line instead.
3. Write the document as a live discussion, not a finished spec: mark unsettled
   decisions with blockquote callouts and close with an open-questions table
   (`Ref | Question | Blocks | Status`). The point is to show what is *not* agreed.
4. Comment with `%%`. Frontmatter `title:` needs Mermaid 9.4+ — prefer a markdown
   heading above the fence.
5. Diagram what is being argued about, not everything that exists. Four focused
   diagrams beat one exhaustive one.
