

  function validHour(x) { return /^([01]\d|2[0-3]):[0-5]\d$/.test(String(x || '')); }

  function normalizeHours(v) {
    if (String(v || '').trim().toLowerCase() === '24/7') return { open: '00:00', close: '00:00', is24Hours: true };
    const parts = String(v || '10:00 - 22:00').replace(/–/g, '-').split('-').map((x) => x.trim());
    return { open: validHour(parts[0]) ? parts[0] : '10:00', close: validHour(parts[1]) ? parts[1] : '22:00', is24Hours: false };
  }

  function isWithinOpeningHours(hoursStr, is24Hours = false) {
    if (is24Hours || String(hoursStr || '').trim() === '24/7') return true;
    const h = normalizeHours(hoursStr);
    const toMin = (t) => { const [hh, mm] = t.split(':').map(Number); return hh * 60 + mm; };
    const openMin = toMin(h.open), closeMin = toMin(h.close);
    const now = new Date(); const nowMin = now.getHours() * 60 + now.getMinutes();
    if (openMin === closeMin) return true; // 24h if open==close
    if (closeMin > openMin) return nowMin >= openMin && nowMin < closeMin;
    return nowMin >= openMin || nowMin < closeMin; // crosses midnight
  }

  function isPastLastTokenTime(lastTokenTime, hoursStr) {
    if (!lastTokenTime) return false;
    const toMin = (t) => { const [hh, mm] = String(t).split(':').map(Number); return hh * 60 + mm; };
    const h = normalizeHours(hoursStr);
    const openMin = toMin(h.open);
    const cutoffMin = toMin(lastTokenTime);
    const now = new Date(); const nowMin = now.getHours() * 60 + now.getMinutes();
    const elapsedNow = (nowMin - openMin + 1440) % 1440;
    const elapsedCutoff = (cutoffMin - openMin + 1440) % 1440;
    return elapsedNow >= elapsedCutoff;
  }


  function normalizePhone(v) {
    // Arabic-Indic (٠-٩) and Persian (۰-۹) digits are what an Arabic
    // keyboard types by default — without converting them first, the
    // filter below deleted every digit and the number was silently lost.
    let x = String(v || '').replace(/[\u0660-\u0669]/g, (d) => String(d.charCodeAt(0) - 0x0660)).replace(/[\u06F0-\u06F9]/g, (d) => String(d.charCodeAt(0) - 0x06F0)).replace(/[^\d+]/g, '');
    if (x.startsWith('00')) x = '+' + x.slice(2);
    if (x.startsWith('+')) x = x.slice(1);
    x = x.replace(/\D/g, '');
    if (x.startsWith('0') && x.length >= 9) x = '971' + x.slice(1);
    return x.slice(0, 15);
  }

  const BLOCKED_WORDS = [
    'كس', 'كسم', 'كسمك', 'طيز', 'زبي', 'زب', 'عرص', 'معرص', 'شرموط', 'شرموطه', 'قحبة', 'خول', 'متناك', 'منيوك', 'كلب ابن', 'ابن الكلب', 'يلعن',
    'fuck', 'shit', 'bitch', 'asshole', 'bastard', 'whore', 'slut', 'cunt', 'dick', 'pussy', 'nigger', 'faggot'
  ];

  const normBad = (s) => String(s || '').toLowerCase().replace(/[\u064B-\u065F\u0670\u0640]/g, '').replace(/[أإآ]/g, 'ا').replace(/ة/g, 'ه').replace(/ى/g, 'ي');

  const BLOCKED_SET = new Set(BLOCKED_WORDS.filter((w) => !w.includes(' ')).map(normBad));

  const BLOCKED_PHRASES = BLOCKED_WORDS.filter((w) => w.includes(' ')).map(normBad);

  function containsInappropriateLanguage(text) {
    if (!text) return false;
    const words = normBad(text).split(/[^a-z0-9\u0621-\u064A]+/).filter(Boolean);
    const forms = (w) => {
      const once = w.replace(/(.)\1+/g, '$1'), twice = w.replace(/(.)\1{2,}/g, '$1$1'), out = [w, once, twice];
      [w, once].forEach((x) => { const a = x.match(/^(?:وال|بال|فال|يا|ال|و|ف|ب)(.{2,})$/); if (a) out.push(a[1]); });
      [w, once, twice].forEach((x) => { const e = x.match(/^([a-z]{3,}?)(ers|er|es|ing|ed|s)$/); if (e) out.push(e[1]); });
      return out;
    };
    if (words.some((w) => forms(w).some((f) => BLOCKED_SET.has(f)))) return true;
    const joined = ' ' + words.join(' ') + ' ';
    return BLOCKED_PHRASES.some((ph) => joined.includes(' ' + ph + ' '));
  }
module.exports={normalizeHours,isWithinOpeningHours,isPastLastTokenTime,normalizePhone,containsInappropriateLanguage};