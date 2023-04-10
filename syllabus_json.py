import os, sys, json, time
import re
from typing import Dict

import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select

from classes import Language, Faculty, Syllabus, Utils, SyllabusEncoder


def get_syllabus(
    utils: Utils,
    language: Language,
    year: str,
    url: str,
    faculty: Faculty,
) -> Syllabus:
    utils.driver.get(url)
    utils.wait_and_find(By.ID, "ctl00_phContents_Detail_LctInfo")

    id = utils.get_inner_text(By.ID, "ctl00_phContents_Detail_lbl_lct_cd")
    html = driver.page_source

    # 部屋情報だけ別のURLから取得
    utils.driver.get(
        f"https://kyomu.office.tut.ac.jp/portal/StudentApp/Lct/LectureList.aspx?lct_year={year}&lct_cd={id}"
    )
    utils.wait_and_find(By.ID, "ctl00_phContents_ucLctList_ucLctHeader_tbRowHeader")
    room = (
        utils.get_inner_text(
            By.CSS_SELECTOR,
            "#ctl00_phContents_ucLctList_gv > tbody > tr:nth-child(2) > td:nth-child(5)",
        )
        or ""
    )
    room = re.sub(r"_.*?$", "", room)

    with open(
        f"./out/{language.value}/{year}/{faculty.value[0]}/{id}.html",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(f"<!-- {room} -->\n")
        f.write(html)


def get_syllabuses_by_faculty(
    utils: Utils,
    language: Language,
    year: str,
    faculty: Faculty,
) -> Dict[str, Syllabus]:
    utils.driver.get("https://kyomu.office.tut.ac.jp/portal/public/syllabus/")

    # 言語選択
    if language == Language.JA:
        utils.wait_and_find(By.ID, "ctl00_bhHeader_slLanguage_imgBtnJpn").click()
    elif language == Language.EN:
        utils.wait_and_find(By.ID, "ctl00_bhHeader_slLanguage_imgBtnEng").click()

    # 年度・学部選択
    Select(utils.wait_and_find(By.ID, "ctl00_phContents_ddl_year")).select_by_value(
        year
    )
    Select(utils.wait_and_find(By.ID, "ctl00_phContents_ddl_fac")).select_by_value(
        faculty.value[1]
    )
    utils.wait_and_find(By.ID, "ctl00_phContents_ctl06_btnSearch").click()

    # シラバスURL一覧
    Select(
        utils.wait_and_find(By.ID, "ctl00_phContents_ucGrid_ddlLines")
    ).select_by_index(0)
    utils.wait_and_find(By.ID, "ctl00_phContents_ucGrid_grv")
    urls = [
        element.get_attribute("href")
        for element in driver.find_elements(
            By.CSS_SELECTOR, "#ctl00_phContents_ucGrid_grv a"
        )
    ]

    syllabuses = {}

    for url in tqdm.tqdm(urls, desc=f"{language.value}/{year}/{faculty.value[0]}"):
        get_syllabus(utils, language, year, url, faculty)
        time.sleep(1)


driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)
utils = Utils(driver, wait)
year = sys.argv[1]

# ログイン
driver.get("https://kyomu.office.tut.ac.jp/portal/")
cookies = driver.get_cookies()
while driver.current_url != "https://kyomu.office.tut.ac.jp/portal/StudentApp/Top.aspx":
    pass
utils.wait_and_find(By.ID, "ctl00_bhHeader_lnkLogout")

# 全シラバス取得・保存
for language in Language:
    for faculty in Faculty:
        os.makedirs(f"./out/{language.value}/{year}/{faculty.value[0]}", exist_ok=True)
        get_syllabuses_by_faculty(utils, language, year, faculty)

driver.quit()
