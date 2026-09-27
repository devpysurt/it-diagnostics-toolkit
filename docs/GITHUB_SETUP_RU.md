# Как опубликовать IT Diagnostics Toolkit на GitHub

Проект уже содержит код, README на английском, тесты, CI, лицензию и учебные отчёты. Создавать каждый файл вручную не нужно: перенеси готовое содержимое в один репозиторий.

## 1. Скачай и распакуй архив

Распакуй `it-diagnostics-toolkit.zip`. Внутри находится папка `it-diagnostics-toolkit`. Открой её: непосредственно внутри должны быть `README.md`, `pyproject.toml`, `src`, `tests` и `docs`.

Архив предназначен для переноса проекта. В сам репозиторий нужно добавить распакованные файлы, а не один ZIP.

## 2. Создай локальный репозиторий через GitHub Desktop

Этот вариант подходит для Windows и macOS. Для Linux ниже есть вариант с Git.

1. Установи [GitHub Desktop](https://desktop.github.com/) и войди в свой GitHub.
2. Выбери **File → New repository…**. На стартовом экране похожая кнопка называется **Create a New Repository on your Hard Drive…**.
3. Заполни поля:

| Поле | Значение |
| --- | --- |
| Name | `it-diagnostics-toolkit` |
| Description | `Read-only IT diagnostics for resource usage, DNS, TCP connectivity and service checks, with HTML and JSON reports.` |
| Local path | Например, `Documents/GitHub` — родительская папка нового проекта |
| Initialize this repository with a README | Не включать: готовый README уже есть |
| Git ignore | `None`: готовый `.gitignore` уже есть |
| License | `None`: готовая MIT-лицензия уже есть в архиве |

4. Нажми **Create repository**. Desktop создаст папку `Documents/GitHub/it-diagnostics-toolkit`.
5. Скопируй **содержимое** распакованной папки в созданную папку репозитория. Избегай лишнего уровня `it-diagnostics-toolkit/it-diagnostics-toolkit`.
6. Перенеси также `.github` и `.gitignore`. На macOS скрытые элементы показываются сочетанием **Command + Shift + .**. Служебную папку `.git`, которую создал Desktop, оставь на месте.

## 3. Проверь, что куда попало

| Путь в репозитории | Что в нём |
| --- | --- |
| `README.md` | Английское описание проекта; автоматически показывается на главной странице |
| `pyproject.toml` | Установка пакета, зависимости и команда `itdiag` |
| `src/it_diagnostics/` | Исходный код программы |
| `tests/` | Автоматические проверки |
| `.github/workflows/ci.yml` | Запуск тестов через GitHub Actions |
| `.gitignore` | Исключение виртуального окружения и настоящих отчётов |
| `config.example.json` | Пример локальных проверок |
| `config.network.example.json` | Пример DNS/TCP-проверок |
| `examples/reports/` | Готовые учебные HTML/JSON-отчёты |
| `docs/images/report-overview.svg` | Иллюстрация учебного отчёта для README |
| `docs/` | Архитектура, кейсы, инструкции, источники и запись о проверках |
| `scripts/generate_examples.py` | Пересоздание учебных отчётов |
| `LICENSE` | Лицензия MIT |

Файлы `.venv`, `reports` и `config.local.json`, которые появятся при работе, публиковать не нужно. Они уже включены в `.gitignore`.

## 4. Запусти проект у себя

Установи Python 3.10 или новее, если его ещё нет. Для первого запуска удобно использовать Python 3.12.

В Windows открой PowerShell в папке проекта и выполни:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m it_diagnostics --demo dns-failure
.\.venv\Scripts\python.exe -m it_diagnostics
```

В Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python -m it_diagnostics --demo dns-failure
.venv/bin/python -m it_diagnostics
```

Первый запуск диагностики выше — учебный, второй собирает доступные показатели твоей системы. Программа напечатает пути к отчётам. Открой HTML в браузере.

Для демонстрации рекрутеру достаточно `examples/reports/dns-failure.html`: его можно открыть даже до установки Python.

## 5. Сделай commit и опубликуй

1. Вернись в GitHub Desktop: файлы должны появиться во вкладке **Changes**.
2. Убедись, что видны `README.md`, исходники и `.github/workflows/ci.yml`.
3. В поле **Summary** введи: `Add diagnostics toolkit, tests and documentation`.
4. Нажми **Commit to main** (название ветки может отличаться).
5. Нажми **Publish repository**.
6. Оставь имя `it-diagnostics-toolkit` и сними **Keep this code private**, если хочешь дать открытый доступ рекрутерам.
7. Выбери личный аккаунт, а не организацию, и нажми **Publish Repository**.
8. Открой **Repository → View on GitHub**.

На сайте должны быть видны папки проекта, английский README и картинка отчёта. Если видна лишь одна вложенная папка, перенеси её содержимое в корень, сделай новый commit и **Push origin**.

## 6. Проверь автоматические тесты

Открой вкладку **Actions**, затем workflow **Tests**. Он запустится при публикации и следующих изменениях кода. Матрица содержит Ubuntu, Windows и macOS, по три версии Python.

Дождись завершения. Зелёные результаты подтвердят проверку на GitHub runners. Если задача красная, открой упавший шаг и прочитай ошибку. Не утверждай, что все платформы проверены, до фактического успешного запуска. Настройка CI сама по себе не означает, что он уже выполнился.

## 7. Оформи страницу проекта

На главной странице репозитория нажми значок настройки возле **About**.

Описание:

```text
Read-only IT diagnostics for resource usage, DNS, TCP connectivity and service checks, with HTML and JSON reports.
```

Topics — добавь по отдельности:

```text
python
it-support
troubleshooting
system-administration
diagnostics
networking
automation
portfolio-project
```

Открой свой профиль → **Customize your pins** → выбери `it-diagnostics-toolkit` → **Save pins**.

Ссылка на проект будет выглядеть так:

```text
https://github.com/YOUR_USERNAME/it-diagnostics-toolkit
```

Здесь `YOUR_USERNAME` замени своим логином GitHub. Других репозиториев, сервера или GitHub Pages для этого проекта создавать не нужно.

## 8. Что показывать на собеседовании

1. Объясни, кому помогает программа: специалисту поддержки при первичной диагностике.
2. Покажи `--demo dns-failure` и объясни, почему TCP не удалось проверить после ошибки разрешения имени.
3. Открой JSON и покажи поля evidence, status и coverage.
4. Объясни разницу между `FAIL` и `SKIP`.
5. Покажи тесты и успешный workflow на своём GitHub.
6. Расскажи об ограничениях: нет проверки SMART, TLS и бизнес-функций приложения.

После собственного запуска и изучения кода проект можно добавить в раздел **Projects** резюме со ссылкой на репозиторий. Назови его личным учебным проектом. Учебные сценарии не являются реальными инцидентами, а результаты программы не нужно представлять как достижения работодателя.

## Альтернатива: публикация через Git

Выбери этот путь вместо Desktop, если Git уже установлен. Не выполняй его повторно поверх публикации через Desktop.

1. На [GitHub](https://github.com/new) создай пустой репозиторий `it-diagnostics-toolkit`. Выбери Public, не добавляй README, `.gitignore` и лицензию на сайте.
2. Открой терминал в распакованной папке с `pyproject.toml`.
3. Настрой автора для этого репозитория и создай commit. Для email можно использовать свой GitHub noreply-адрес из **Settings → Emails**.

```bash
git init -b main
git config user.name "Stanislav Delov"
git config user.email "YOUR_GITHUB_EMAIL"
git add .
git commit -m "Add diagnostics toolkit, tests and documentation"
git remote add origin https://github.com/YOUR_USERNAME/it-diagnostics-toolkit.git
git push -u origin main
```

Замени `YOUR_GITHUB_EMAIL` и `YOUR_USERNAME` перед запуском. GitHub может запросить вход через браузер или credential manager. Обычный пароль аккаунта не используется как пароль для Git по HTTPS; следуй официальному способу аутентификации. Если настройка Git незнакома, Desktop упрощает этот этап.

## Как обновлять проект позже

Измени нужные файлы в локальном репозитории → запусти тесты → открой **Changes** в Desktop → напиши краткое описание → **Commit to main** → **Push origin**. Для правок кода переустанови проект или используй editable-установку `python -m pip install -e ".[dev]"`.

## Официальные инструкции

- [Создание первого репозитория через Desktop](https://docs.github.com/en/desktop/overview/creating-your-first-repository-using-github-desktop)
- [Публикация локального проекта](https://docs.github.com/en/desktop/adding-and-cloning-repositories/adding-an-existing-project-to-github-using-github-desktop)
- [Публикация через Git](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)
- [Topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)
- [Закрепление проекта в профиле](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/pinning-items-to-your-profile)
