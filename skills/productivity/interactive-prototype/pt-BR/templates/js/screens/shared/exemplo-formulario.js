/* Tela de EXEMPLO de formulário — renomear/substituir pela primeira tela real do fluxo.
   Contrato de tela: screenXxx() devolve o HTML; validateXxx() (opcional, registrada em
   screenValidators) devolve true/false e mostra os erros junto dos campos. */

function screenExemploFormulario(){
  return `<div class="eyebrow">Etapa de exemplo</div>
    <h2 class="screen-title">Seus dados</h2>
    <p class="screen-subtitle">Formulário de exemplo com validação inline.</p>
    ${fieldHTML('nome', 'Nome', { required: true })}
    ${fieldHTML('email', 'E-mail', { type: 'email', required: true, placeholder: 'voce@exemplo.com' })}`;
}

function validateExemploFormulario(){
  let ok = true;
  if (!formState.nome?.trim()){ showFieldError('nome', 'Informe seu nome'); ok = false; }
  if (!/^\S+@\S+\.\S+$/.test(formState.email || '')){ showFieldError('email', 'Informe um e-mail válido'); ok = false; }
  return ok;
}
