from pyspark.sql import SparkSession
import matplotlib.pyplot as plt
import seaborn as sns

from scrap_articles.spiders.utils import check_state

sns.set()

save_dir = "/Users/mouadk/Desktop/Spark/"

spark = SparkSession \
    .builder \
    .appName("visualizeArticles") \
    .config("spark.mongodb.input.uri", "mongodb://127.0.0.1/articles.articles") \
    .config("spark.mongodb.output.uri", "mongodb://127.0.0.1/articles_out.coll") \
    .getOrCreate()

df = spark.read.format("mongo").load()
pandasDF = df.toPandas()

pandasDF.drop('_id', axis=1, inplace=True)
pandasDF.date = pandasDF.date.dt.strftime('%Y-%m-%d')
pandasDF.to_json(f"{save_dir}articles.json")



for index, row in pandasDF.iterrows():
    for uni in row['universities']:
        state = uni.split(",")[-1].strip()
        if check_state(state) and "USA" in pandasDF.iloc[index, 4]:
            pandasDF.iloc[index, 4].append("USA")

    pandasDF.iloc[index, 4] = ";".join(pandasDF.iloc[index, 4])
    pandasDF.iloc[index, 2] = ";".join(pandasDF.iloc[index, 2])
#
pandasDF.drop('_id', axis=1, inplace=True)
pandasDF.to_csv(f"{save_dir}articles.csv", index=False)


print(f"Nombre d'article totale: {len(pandasDF)}")

print(f"Sources des articles:")
print(pandasDF.source.value_counts())

df.createOrReplaceTempView("articles")

sources = spark.sql("select source, count(*) as count from articles group by source").toPandas()
labels = sources.loc[:, 'source']
values = sources.loc[:, 'count']


pie, ax = plt.subplots(figsize=[10, 6])
plt.pie(x=values, autopct="%.1f%%", explode=[0.05]*3, labels=labels, pctdistance=0.5)
plt.title("Articles' sources", fontsize=14)
pie.savefig(f"{save_dir}article_sources.png")


pie, ax = plt.subplots(figsize=[10, 6])
years = pandasDF.date.groupby(pandasDF.date.dt.year).size().reset_index(name='count')
sns.lineplot(data=years, x="date", y="count").get_figure().savefig(f"{save_dir}by_years.png")

countries = {}
total_counties = 0

unis = {}
total_unis = 0
for index, row in pandasDF.iterrows():
    for country in row['countries']:
        total_counties += 1
        if country not in countries:
            countries[country] = 1
        else:
            countries[country] += 1

    for uni in row['universities']:
        total_unis += 1
        if uni not in unis:
            unis[uni] = 1
        else:
            unis[uni] += 1
print(f"total_unis {total_unis}")
countries['others'] = 0
unis['others'] = 0

for country in list(countries):
    if countries[country] < total_counties * 0.015:
        countries['others'] += countries[country]
        countries.pop(country)

for uni in list(unis):
    if unis[uni] < 2:
        unis['others'] += unis[uni]
        unis.pop(uni)

pie, ax = plt.subplots(figsize=[10, 6])
plt.pie(x=countries.values(), autopct="%.1f%%", labels=countries.keys(), pctdistance=0.5, explode=[0.1] * len(countries.keys()))
plt.title("By countries", fontsize=14)
pie.savefig(f"{save_dir}By_countries.png")

unis = dict(sorted(unis.items(), key=lambda item: item[1]))

print("Les universites avec les plus de contributions:")
for i in range(5):
    print(f'{i+1}- {list(unis.keys())[i]}')
