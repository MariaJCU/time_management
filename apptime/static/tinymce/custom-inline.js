
var useDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;

tinymce.init({
  selector: '#textarea-pop',
  promotion: false,
  plugins: 'print paste importcss searchreplace autolink autosave directionality code visualblocks visualchars fullscreen image link codesample table charmap hr nonbreaking insertdatetime advlist lists wordcount textpattern noneditable help charmap quickbars emoticons media',
  menubar: '',
  toolbar: 'bold italic underline strikethrough | alignleft aligncenter alignright alignjustify | fullscreen',
  toolbar_sticky: true,
  autosave_ask_before_unload: true,
  autosave_interval: '30s',
  autosave_prefix: '{path}{query}-{id}-',
  autosave_restore_when_empty: false,
  autosave_retention: '2m',
  image_advtab: true,
  importcss_append: true,
  image_caption: true,
  media_live_embeds: true,
  noneditable_noneditable_class: 'mceNonEditable',
  toolbar_mode: 'sliding',
  skin: useDarkMode ? 'oxide-dark' : 'oxide',
  content_css: useDarkMode ? 'dark' : 'default',
  content_style: 'body { font-family:Helvetica,Arial,sans-serif; font-size:14px }'
 });


