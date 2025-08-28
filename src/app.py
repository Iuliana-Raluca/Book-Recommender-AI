
import gradio as gr
from main import respond, TITLES
from tool import generate_book_cover, generate_speech


with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue", secondary_hue="purple")) as app:
    gr.Markdown("""
    <style>
    body, .gradio-container {
        background: #f7f8fa !important;
    }
    #header {
        background: #fff;
        border-radius: 16px;
        box-shadow: 0 2px 12px #e0e0e0;
        padding: 24px 32px 16px 32px;
        margin-bottom: 24px;
    }
    #input-box textarea {
        background: #f0f4ff;
        border-radius: 8px;
        font-size: 1.1em;
    }
    #output-box textarea {
        background: #f8f8ff;
        border-radius: 8px;
        font-size: 1.1em;
    }
    #submit-btn, #cover-btn, #tts-btn {
        background: linear-gradient(90deg,#6c63ff,#48c6ef);
        color: #fff;
        border-radius: 8px;
        font-weight: bold;
        box-shadow: 0 2px 8px #e0e0e0;
        transition: background 0.2s;
    }
    #submit-btn:hover, #cover-btn:hover, #tts-btn:hover {
        background: linear-gradient(90deg,#48c6ef,#6c63ff);
    }
    #cover-img img {
        border-radius: 16px;
        box-shadow: 0 4px 24px #d1d1d1;
    }
    </style>
    <div style='display:flex;align-items:center;gap:16px;'>
        <img src='https://img.icons8.com/fluency/48/book.png' style='height:48px;'>
        <h1 style='margin:0;color:#3b3b3b;'>Book Recommender <span style="color:#6c63ff"></span></h1>
    </div>
    <p style='color:#48c6ef;font-size:1.1em;'>Cere o recomandare și primește un rezumat, copertă și audio!</p>
    """, elem_id="header")

    state_title = gr.State()

    with gr.Row():
        with gr.Column(scale=2):
            with gr.Group():
                user_input = gr.Textbox(
                    label="📚 Întrebare",
                    lines=4,
                    placeholder="Ex: Vreau o carte despre libertate și control",
                    elem_id="input-box"
                )
                submit_btn = gr.Button("🚀 Trimite", size="sm", variant="primary", elem_id="submit-btn")
            output = gr.Textbox(
                label="📝 Recomandare și rezumat",
                lines=10,
                elem_id="output-box"
            )

            with gr.Row():
                tts_btn = gr.Button("🔊 Redă audio", visible=False, elem_id="tts-btn")
                tts_audio = gr.Audio(type="filepath", visible=False, elem_id="tts-audio")

            generate_btn = gr.Button("🎨 Generează coperta", visible=True, elem_id="cover-btn")

        with gr.Column(scale=1):
            image_output = gr.Image(
                visible=False,
                type="filepath",
                height=360,
                elem_id="cover-img"
            )



    def handle_submit(input_text):
        response = respond(input_text)
        title_found = None
        for title in TITLES:
            if title.lower() in response.lower():
                title_found = title
                break
        return (
            response,
            title_found,
            gr.update(visible=False),  
            gr.update(visible=True),  
            gr.update(visible=False)   
        )


    def handle_image(title):
        image_path = generate_book_cover(title)
        return image_path, gr.update(visible=True)


    def handle_speech(text):
        audio_path = generate_speech(text)
        return audio_path, gr.update(visible=True)



    submit_btn.click(
        fn=handle_submit,
        inputs=[user_input],
        outputs=[output, state_title, image_output, tts_btn, tts_audio]
    )

    generate_btn.click(
        fn=handle_image,
        inputs=[state_title],
        outputs=[image_output, image_output]
    )

    tts_btn.click(
        fn=handle_speech,
        inputs=[output],
        outputs=[tts_audio, tts_audio]
    )

if __name__ == "__main__":
    app.launch()
