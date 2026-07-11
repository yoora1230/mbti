from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ---------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="MBTI World Finder",
    page_icon="🌍",
    layout="wide",
)

MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP",
]

MBTI_COLORS = {
    "INTJ": "#6C5CE7", "INTP": "#6C5CE7", "ENTJ": "#6C5CE7", "ENTP": "#6C5CE7",
    "INFJ": "#00B894", "INFP": "#00B894", "ENFJ": "#00B894", "ENFP": "#00B894",
    "ISTJ": "#0984E3", "ISFJ": "#0984E3", "ESTJ": "#0984E3", "ESFJ": "#0984E3",
    "ISTP": "#E17055", "ISFP": "#E17055", "ESTP": "#E17055", "ESFP": "#E17055",
}

MBTI_GROUPS = {
    "분석가형": ["INTJ", "INTP", "ENTJ", "ENTP"],
    "외교관형": ["INFJ", "INFP", "ENFJ", "ENFP"],
    "관리자형": ["ISTJ", "ISFJ", "ESTJ", "ESFJ"],
    "탐험가형": ["ISTP", "ISFP", "ESTP", "ESFP"],
}

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1250px;
        }
        .hero {
            padding: 2rem 2.2rem;
            border-radius: 24px;
            background: linear-gradient(135deg, #6C5CE7 0%, #0984E3 100%);
            color: white;
            margin-bottom: 1.4rem;
            box-shadow: 0 12px 30px rgba(70, 70, 160, 0.18);
        }
        .hero h1 {
            margin: 0;
            font-size: 2.45rem;
        }
        .hero p {
            margin: 0.7rem 0 0 0;
            font-size: 1.05rem;
            opacity: 0.92;
        }
        .notice {
            border-left: 5px solid #6C5CE7;
            background: rgba(108, 92, 231, 0.08);
            padding: 0.9rem 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(128, 128, 128, 0.07);
            border: 1px solid rgba(128, 128, 128, 0.16);
            padding: 1rem;
            border-radius: 16px;
        }
        .footer {
            text-align: center;
            opacity: 0.65;
            margin-top: 2rem;
            font-size: 0.9rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 데이터 불러오기
# ---------------------------------------------------------
@st.cache_data
def load_mbti_data() -> pd.DataFrame:
    """현재 폴더에서 MBTI 국가 데이터 CSV를 자동으로 찾는다."""
    csv_files = list(Path(".").glob("*.csv"))

    # 파일명에 countriesMBTI가 포함된 파일을 우선 탐색
    csv_files.sort(
        key=lambda path: (
            "countriesmbti" not in path.name.lower(),
            path.name.lower(),
        )
    )

    required_columns = {"Country", *MBTI_TYPES}
    errors = []

    for csv_path in csv_files:
        for encoding in ("utf-8-sig", "utf-8", "cp949"):
            try:
                data = pd.read_csv(csv_path, encoding=encoding)
                data.columns = [str(column).strip() for column in data.columns]

                if required_columns.issubset(data.columns):
                    cleaned = data[["Country", *MBTI_TYPES]].copy()
                    cleaned["Country"] = cleaned["Country"].astype(str).str.strip()

                    for mbti in MBTI_TYPES:
                        cleaned[mbti] = pd.to_numeric(
                            cleaned[mbti], errors="coerce"
                        )

                    cleaned = cleaned.dropna(subset=["Country", *MBTI_TYPES])
                    cleaned = cleaned[cleaned["Country"] != ""]
                    return cleaned.reset_index(drop=True)

            except Exception as error:
                errors.append(f"{csv_path.name}: {error}")

    raise FileNotFoundError(
        "MBTI 데이터 CSV를 찾지 못했습니다. "
        "main.py와 같은 GitHub 폴더에 CSV 파일을 업로드해 주세요."
    )


try:
    df = load_mbti_data()
except Exception as error:
    st.error(str(error))
    st.info(
        "CSV에는 Country 열과 16개 MBTI 열이 있어야 합니다. "
        "예: Country, INFJ, ISFJ, INTP, ..."
    )
    st.stop()


# 데이터가 0~1 비율이면 퍼센트로 변환하고,
# 이미 0~100 값이면 그대로 사용한다.
if df[MBTI_TYPES].max().max() <= 1.5:
    percent_df = df.copy()
    percent_df[MBTI_TYPES] = percent_df[MBTI_TYPES] * 100
else:
    percent_df = df.copy()


# ---------------------------------------------------------
# 화면 상단
# ---------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>🌍 MBTI World Finder</h1>
        <p>나와 같은 MBTI 유형의 비율이 높은 나라를 세계 지도와 순위로 찾아보세요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="notice">
        이 데이터에는 국가별 인구수가 없으므로, 실제 사람 수가 아닌
        <b>각 나라에서 해당 MBTI가 차지하는 비율</b>을 기준으로 비교합니다.
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 사이드바
# ---------------------------------------------------------
with st.sidebar:
    st.header("🔎 MBTI 선택")

    selected_mbti = st.selectbox(
        "나의 MBTI",
        MBTI_TYPES,
        index=MBTI_TYPES.index("ENFP"),
    )

    ranking_count = st.slider(
        "순위에 표시할 국가 수",
        min_value=5,
        max_value=min(30, len(percent_df)),
        value=10,
        step=1,
    )

    st.divider()
    st.subheader("MBTI 그룹")

    selected_group = next(
        group
        for group, types in MBTI_GROUPS.items()
        if selected_mbti in types
    )
    st.write(f"**{selected_mbti}**는 **{selected_group}**에 속합니다.")

    st.caption(
        "CSV 파일은 main.py와 같은 GitHub 저장소 폴더에 넣어 주세요."
    )


# ---------------------------------------------------------
# 선택 MBTI 분석
# ---------------------------------------------------------
ranking = (
    percent_df[["Country", selected_mbti]]
    .sort_values(selected_mbti, ascending=False)
    .reset_index(drop=True)
)
ranking.index = ranking.index + 1
ranking.index.name = "순위"

top_country = ranking.iloc[0]["Country"]
top_rate = ranking.iloc[0][selected_mbti]
average_rate = ranking[selected_mbti].mean()
median_rate = ranking[selected_mbti].median()

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric("🥇 비율이 가장 높은 나라", top_country)
metric2.metric("📊 1위 국가 비율", f"{top_rate:.2f}%")
metric3.metric("🌐 전체 국가 평균", f"{average_rate:.2f}%")
metric4.metric("🗺️ 분석 국가 수", f"{len(percent_df)}개")


# ---------------------------------------------------------
# 지도와 상위 순위
# ---------------------------------------------------------
map_tab, ranking_tab, country_tab, compare_tab = st.tabs(
    ["세계 지도", "국가 순위", "나라별 MBTI", "MBTI 비교"]
)

with map_tab:
    st.subheader(f"{selected_mbti} 비율 세계 지도")

    map_df = ranking.reset_index()

    fig_map = px.choropleth(
        map_df,
        locations="Country",
        locationmode="country names",
        color=selected_mbti,
        hover_name="Country",
        hover_data={
            selected_mbti: ":.2f",
            "순위": True,
            "Country": False,
        },
        color_continuous_scale="Purples",
        labels={selected_mbti: f"{selected_mbti} 비율(%)"},
    )
    fig_map.update_geos(
        showframe=False,
        showcoastlines=True,
        projection_type="natural earth",
    )
    fig_map.update_layout(
        height=580,
        margin=dict(l=0, r=0, t=20, b=0),
        coloraxis_colorbar_title=f"{selected_mbti}<br>비율(%)",
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.caption(
        "일부 국가명은 지도 서비스의 표준 국가명과 다르면 색칠되지 않을 수 있습니다."
    )


with ranking_tab:
    left, right = st.columns([1.2, 1])

    with left:
        st.subheader(f"{selected_mbti} 상위 {ranking_count}개 국가")

        top_n = ranking.head(ranking_count).sort_values(
            selected_mbti, ascending=True
        )

        fig_bar = px.bar(
            top_n.reset_index(),
            x=selected_mbti,
            y="Country",
            orientation="h",
            text=selected_mbti,
            labels={
                selected_mbti: f"{selected_mbti} 비율(%)",
                "Country": "국가",
            },
        )
        fig_bar.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside",
            marker_color=MBTI_COLORS[selected_mbti],
        )
        fig_bar.update_layout(
            height=max(430, ranking_count * 38),
            showlegend=False,
            margin=dict(l=0, r=30, t=10, b=0),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with right:
        st.subheader("전체 순위표")

        display_ranking = ranking.copy()
        display_ranking[selected_mbti] = display_ranking[selected_mbti].map(
            lambda value: f"{value:.2f}%"
        )
        display_ranking = display_ranking.rename(
            columns={
                "Country": "국가",
                selected_mbti: f"{selected_mbti} 비율",
            }
        )

        st.dataframe(
            display_ranking,
            use_container_width=True,
            height=470,
        )

        csv_download = ranking.reset_index().to_csv(
            index=False, encoding="utf-8-sig"
        )
        st.download_button(
            "📥 순위 CSV 다운로드",
            data=csv_download,
            file_name=f"{selected_mbti}_country_ranking.csv",
            mime="text/csv",
            use_container_width=True,
        )


with country_tab:
    st.subheader("한 나라의 MBTI 분포 살펴보기")

    selected_country = st.selectbox(
        "나라 선택",
        sorted(percent_df["Country"].unique()),
    )

    country_row = percent_df.loc[
        percent_df["Country"] == selected_country, MBTI_TYPES
    ].iloc[0]

    country_profile = (
        country_row.rename_axis("MBTI")
        .reset_index(name="비율")
        .sort_values("비율", ascending=False)
    )

    country_top_mbti = country_profile.iloc[0]["MBTI"]
    country_top_rate = country_profile.iloc[0]["비율"]

    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric("가장 높은 MBTI", country_top_mbti)
        st.metric("해당 비율", f"{country_top_rate:.2f}%")
        st.metric(
            f"{selected_mbti} 국가 순위",
            f"{ranking.index[ranking['Country'] == selected_country][0]}위",
        )

        table_profile = country_profile.copy()
        table_profile["비율"] = table_profile["비율"].map(
            lambda value: f"{value:.2f}%"
        )
        st.dataframe(
            table_profile,
            hide_index=True,
            use_container_width=True,
            height=380,
        )

    with col2:
        fig_country = px.bar(
            country_profile.sort_values("비율"),
            x="비율",
            y="MBTI",
            orientation="h",
            text="비율",
            title=f"{selected_country}의 MBTI 분포",
        )
        fig_country.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside",
        )
        fig_country.update_layout(
            height=580,
            showlegend=False,
            margin=dict(l=0, r=30, t=50, b=0),
            xaxis_title="비율(%)",
            yaxis_title="MBTI",
        )
        st.plotly_chart(fig_country, use_container_width=True)


with compare_tab:
    st.subheader("두 MBTI가 많은 나라 비교하기")

    compare_col1, compare_col2 = st.columns(2)

    with compare_col1:
        mbti_x = st.selectbox(
            "첫 번째 MBTI",
            MBTI_TYPES,
            index=MBTI_TYPES.index(selected_mbti),
            key="mbti_x",
        )

    with compare_col2:
        default_y = "INFP" if selected_mbti != "INFP" else "ENTP"
        mbti_y = st.selectbox(
            "두 번째 MBTI",
            MBTI_TYPES,
            index=MBTI_TYPES.index(default_y),
            key="mbti_y",
        )

    compare_df = percent_df[["Country", mbti_x, mbti_y]].copy()
    compare_df["차이"] = compare_df[mbti_x] - compare_df[mbti_y]

    fig_scatter = px.scatter(
        compare_df,
        x=mbti_x,
        y=mbti_y,
        hover_name="Country",
        hover_data={"차이": ":.2f"},
        labels={
            mbti_x: f"{mbti_x} 비율(%)",
            mbti_y: f"{mbti_y} 비율(%)",
        },
        title=f"{mbti_x}와 {mbti_y} 국가별 비율 비교",
    )

    max_axis = max(
        compare_df[mbti_x].max(),
        compare_df[mbti_y].max(),
    ) * 1.05

    fig_scatter.add_trace(
        go.Scatter(
            x=[0, max_axis],
            y=[0, max_axis],
            mode="lines",
            line=dict(dash="dash", color="gray"),
            name="두 비율이 같음",
            hoverinfo="skip",
        )
    )
    fig_scatter.update_layout(
        height=560,
        margin=dict(l=0, r=0, t=60, b=0),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    diff_col1, diff_col2 = st.columns(2)

    with diff_col1:
        st.markdown(f"#### {mbti_x}가 상대적으로 더 높은 나라")
        x_higher = compare_df.nlargest(5, "차이")[
            ["Country", mbti_x, mbti_y, "차이"]
        ].copy()
        x_higher.columns = ["국가", mbti_x, mbti_y, "비율 차이"]
        st.dataframe(x_higher, hide_index=True, use_container_width=True)

    with diff_col2:
        st.markdown(f"#### {mbti_y}가 상대적으로 더 높은 나라")
        y_higher = compare_df.nsmallest(5, "차이")[
            ["Country", mbti_x, mbti_y, "차이"]
        ].copy()
        y_higher["차이"] = -y_higher["차이"]
        y_higher.columns = ["국가", mbti_x, mbti_y, "비율 차이"]
        st.dataframe(y_higher, hide_index=True, use_container_width=True)


st.markdown(
    """
    <div class="footer">
        MBTI World Finder · Streamlit으로 제작
    </div>
    """,
    unsafe_allow_html=True,
)
