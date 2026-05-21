const preparoForm = document.getElementById('preparo-form');
const preparoResult = document.getElementById('preparo-result');
const padronizacaoForm = document.getElementById('padronizacao-form');
const padronizacaoResult = document.getElementById('padronizacao-result');
const adminForm = document.getElementById('admin-form');
const adminResult = document.getElementById('admin-result');
const tabButtons = document.querySelectorAll('.tab-button');
const tabPanels = document.querySelectorAll('.tab-panel');

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function renderError(container, message) {
  container.classList.remove('hidden');
  container.innerHTML = `<div class="error-box">${escapeHtml(message)}</div>`;
}

function renderSuccess(container, message) {
  container.classList.remove('hidden');
  container.innerHTML = `<div class="success-box">${escapeHtml(message)}</div>`;
}

async function refreshSelectOptions() {
  try {
    const response = await fetch('/api/configuracao');
    const data = await response.json();

    const preparoSelect = document.querySelector('#preparo-form select[name="substancia"]');
    const padronizacaoSelect = document.querySelector('#padronizacao-form select[name="substancia"]');

    if (preparoSelect) {
      preparoSelect.innerHTML = data.preparo.map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join('');
    }
    if (padronizacaoSelect) {
      padronizacaoSelect.innerHTML = data.padronizacao.map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join('');
    }
  } catch (error) {
    console.warn('Não foi possível atualizar as opções de substância.', error);
  }
}

function renderWikiLink(url) {
  if (!url) return '';
  return `
    <div class="info-link-row">
      <a class="info-link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">
        Mais informações na Wikipédia
      </a>
    </div>
  `;
}

function renderMethod(method) {
  if (!method) return '';
  const procedureBlock = method.procedimento
    ? `<pre>${escapeHtml(method.procedimento)}</pre>`
    : '';

  return `
    <article class="method ${escapeHtml(method.status)}">
      <h3>${escapeHtml(method.titulo)}</h3>
      <p><strong>${escapeHtml(method.resumo)}</strong></p>
      ${procedureBlock}
    </article>
  `;
}

preparoForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(preparoForm);
  const payload = Object.fromEntries(formData.entries());

  try {
    const response = await fetch('/api/preparo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error(data.erro || 'Erro ao calcular preparo.');
    }

    preparoResult.classList.remove('hidden');
    preparoResult.innerHTML = `
      <h2>Resultado do preparo</h2>
      <div class="kpi">
        <div class="kpi-item">
          <span class="label">Substância</span>
          <span class="value">${escapeHtml(data.substancia)}</span>
        </div>
        <div class="kpi-item">
          <span class="label">${escapeHtml(data.rotulo)}</span>
          <span class="value">${escapeHtml(data.valor)} ${escapeHtml(data.unidade)}</span>
        </div>
      </div>
      ${renderWikiLink(data.wikipedia_url)}
      <h3>Procedimento sugerido</h3>
      <pre>${escapeHtml(data.procedimento)}</pre>
    `;
  } catch (error) {
    renderError(preparoResult, error.message || 'Erro ao calcular preparo.');
  }
});

padronizacaoForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(padronizacaoForm);
  const payload = Object.fromEntries(formData.entries());

  try {
    const response = await fetch('/api/padronizacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error(data.erro || 'Erro ao calcular padronização.');
    }

    padronizacaoResult.classList.remove('hidden');
    padronizacaoResult.innerHTML = `
      <h2>Resultado da padronização</h2>
      <div class="kpi">
        <div class="kpi-item">
          <span class="label">Substância</span>
          <span class="value">${escapeHtml(data.substancia)}</span>
        </div>
        <div class="kpi-item">
          <span class="label">Concentração</span>
          <span class="value">${escapeHtml(data.concentracao)} mol/L</span>
        </div>
        <div class="kpi-item">
          <span class="label">Volume de viragem</span>
          <span class="value">${escapeHtml(data.volume_viragem)} mL</span>
        </div>
      </div>
      ${renderWikiLink(data.wikipedia_url)}
      <div class="method-grid">
        ${renderMethod(data.metodo_1)}
        ${renderMethod(data.metodo_2)}
      </div>
    `;
  } catch (error) {
    renderError(padronizacaoResult, error.message || 'Erro ao calcular padronização.');
  }
});

function setAdminFields() {
  const selectedType = adminForm?.querySelector('select[name="tipo"]')?.value || 'preparo';
  const preparoFields = document.getElementById('preparo-fields');
  const padronizacaoFields = document.getElementById('padronizacao-fields');

  if (preparoFields) {
    preparoFields.classList.toggle('hidden', selectedType !== 'preparo');
  }
  if (padronizacaoFields) {
    padronizacaoFields.classList.toggle('hidden', selectedType !== 'padronizacao');
  }
}

adminForm?.addEventListener('change', (event) => {
  if (event.target.name === 'tipo') {
    setAdminFields();
  }
});

setAdminFields();

adminForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(adminForm);
  const payload = Object.fromEntries(formData.entries());

  try {
    const response = await fetch('/api/compounds', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error(data.erro || 'Erro ao salvar o composto.');
    }

    renderSuccess(adminResult, data.mensagem || 'Composto salvo com sucesso.');
    await refreshSelectOptions();
    adminForm.reset();
    setAdminFields();
  } catch (error) {
    renderError(adminResult, error.message || 'Erro ao salvar o composto.');
  }
});

tabButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const target = button.dataset.tab;

    tabButtons.forEach((item) => item.classList.toggle('active', item === button));
    tabPanels.forEach((panel) => panel.classList.toggle('active', panel.id === target));
  });
});

refreshSelectOptions();
