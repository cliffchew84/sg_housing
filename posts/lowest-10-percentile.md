---
date: "2025-04-25"
published: true
tags:
  - Public Housing
title: Studying Singapore's cheapest public resale flats since the early 2000s
description: Enough with looking at expensive public resale flats in Singapore! Let's analysis the cheaper resale flats to understand more about them!
---

##### The Background
In Singapore, there has been a lot of discussions about million dollar public flats, about general public housing affordability. I personally did a few such analyses myself, using data from [data.gov.sg](https://www.data.gov.sg). This time, I wanted to do something a bit different, by analysing the price trends of the lowest 10th percentile of resale public homes in Singapore, and to see how they have changed over the years. **All charts are interactive. Clicking on chart legend selects and un-selects it from the chart. This content is best viewed on a desktop.** 

To define this **lowest 10th percentile**, I took the lowest 10th percentile of public resale prices **for each month**. Selecting the lowest 10th percentile prices by months, quarters or years will select different 10th percentile prices. For me, choosing by months was a matter of convenience.

##### General Trends
From 2000 to 2024, we see that our cutoff for the 10th percentile resale prices rose quite a bit, from around 130-150K SGD to its peak of 400K SGD in Dec 2024. However, during this period of rising prices, there was a notable dip from around May 2013 to July 2020, where this 10th percentile cutoff dropped from 340K SGD to 260K SGD.

<iframe src="/static/img/lowest/10p_cutoff.html" width="900" height="620"></iframe>

##### All Lowest 10th Percentile Resale Prices
Next, I plotted a box plot that shows all the resale prices that we at or below the 10th percentile public resale prices. This shows the resale public prices that were the lowest 10th percentile or below. From 2000 to 2024, the prices suggest that there is widening difference even among the lowest 10th percentile public resale prices.

<iframe src="/static/img/lowest/10p_boxplot.html" width="900" height="620"></iframe>

We can see three distinct regions:

- <> Jan 2010 to Apr 2013, where the lowest 10th percentile resale prices were generally rising.
- <> May 2013 to Mar 2020, where the lowest 10th percentile resale prices were generally declining.
- <> Apr 2020 to Dec 2024, where the lowest 10th percentile resale prices were rising rapidly.

Base on these pricing trends, my analysis from here onwards will start from 2010
instead, which I feel is a more interesting timeline to start from.


##### Remaining Lease
For these lowest 10th percentile resale prices, I wanted to compare their remaining lease ( years ) with their resale prices across several selected years, namely 2010, 2015, 2020 and 2024. This was to allow me to see how the relationship between remaining lease and resale prices have changed across the years. **Again, feel free to click on the years of the chart’s legend to select and remove the scatter plot of that year.**

<iframe src="/static/img/lowest/10p_scatter.html" width="900" height="620"></iframe>

Selecting only 2024 and 2010, we can see how distinctively different these two years are. Firstly, we can see that the resale prices of these lowest 10th percentile resale prices were generally higher than those of 2010. This is as seen from the boxplot earlier on. Secondly, in 2010, the remaining lease and resale prices clustered somewhere in the middle of the chart, while the 2024 remaining lease and resale prices had two clusters: (1) a larger one where the resale flats’ remaining lease ranged from **40 to 65 years**, and (2) a smaller cluster where the resale flats’ remaining lease ranged from **82 to 96 years**. While 2010 also had a seemingly smaller cluster of resale flats with more remaining lease, its remaining lease range was somewhere around **70 to 85 years**.

Clicking through the years of 2010, 2015, 2020 to 2024, we can see the gradual creation of these two cluster patterns across the years.

Note that Singapore public homeowners can only sell their flats after occupying their public homes for at least 5 years, whether they bought it directly from the Singapore government or from the resale market.  This meant that even among these lowest 10th percentile public resale prices, there is a growing trend of these public homeowners selling their public homes on the resale market not long after they are able to. 

Granted that many of these public flat owners could have changing life plans and aspirations, such as getting married or having a kid and deciding to upgrade to a larger housing unit. However, comparing to the past years, it is still interesting to wonder if many Singaporeans are buying these Built-To-Order ( BTO ) flats directly from the Singapore government with the main objective of selling them at the resale market for a sizable profit. This is because to ensure public home prices are affordable, BTO public flats are always sold at high subsidized rates, while allowing the homeowner to later sell it at the resale market for profit. 


##### Remaining Lease and CPF usage 
This idea for this piece started from a conversation with a single male friend in his late 30s who was looking for his own home in the Singapore public housing resale market. He told me our Singapore Central Provident Fund ( CPF ), which is our own retirement fund, suggests that the remaining lease of a purchased public home should cover the homeowner until his or her [age of 95](https://www.cpf.gov.sg/service/article/why-do-i-need-to-have-lease-coverage-until-age-95-for-maximum-cpf-usage). **That was a criteria for his resale public home.**

Based on this, a single aged 35 and 40 years old should buy a house with at least 60 and 55 years of lease left. I do know that Singaporeans’ life expectancy is slightly below 90 years old, but I will stick to our CPF’s recommendation for the rest of my analysis. In my updated scatter plot below, I added two such vertical lines. I also added two arbitrary reference horizontal lines to show SGD 300K and SGD 350K prices. 

<iframe src="/static/img/lowest/10p_scatter_w_lines.html" width="900" height="620"></iframe>

One can say a huge portion of resale flats sold in 2024 ( *left light blue region* ) were too old for single individuals aged 40 and above ( based on the CPF’s lease suggestion ). On the other hand, there are clusters of resale flats that not only fit the strict CPF remaining lease criteria, some of them felt between the SGD 300K and SGD 350K budget. Naturally, this scatter plot cannot show other important attributions like location and size. For a single, I assume they may not be too concerned about a small house, but a working single would be more concerned about the housing’s location. 


##### Parting Remarks One
**Singles buying resale public flats** - The CPF lease recommendation feels a bit extreme, as Singapore’s current life expectancy is below 90 years old. However, it also makes sense for a government agency to provide a more cautious recommendation, to ensure the homeowner doesn’t outlive their public homes. Any single who took up the CPF recommendation and bought a resale market in 2024 would need a budget of at least SGD 300K, regardless of the flat's size and location. This of course isn't paid in cash upfront.

##### Parting Remarks Two
**For living or investment** - Before this analysis, I expected all of the resale flats in the lowest 10th percentile of our resale flats to have not much lease left. And while this is true for the major cluster of such flats, the smaller cluster of resale flats with high remaining lease is quite unexpected to me, especially when public homeowners can sell their flats only after living in it for a minimum of 5 years. Maybe the modern fast changing nature of a Singaporean lifestyle is forcing homeowners to upsize their homes more quickly than in the past. **Nonetheless, I cannot help to wonder if more Singaporeans are buying our highly subsidized public homes directly from our Singapore government with the sole intention to sell them as soon as they can in the resale market for a quick profit.** If so, personally, I feel that this differs from the original intent of our public housing policies, which is to give all Singaporeans an opportunity to own a piece of quality housing in Singapore. 

##### Parting Remarks Three
**Overall Market Patterns** - Those quick on their feet might be thinking *"Hey, you are seeing this in the
lowest 10th percentile, is this pattern reflected when I look at the entire
resale public housing market?"* **The short answer is no**, and here is the chart to
show what I see. 

<iframe src="/static/img/lowest/full_scatterplot.html" width="900" height="620"></iframe>

I did try to give this a thought. ***My hypothesis is this shows up only when looking at the lowest 10th percentile of public resale flats because they are formed by a more consistent and well defined user segments: (1) Those that are ok with buying public homes with much lesser leases, and (2) those that want to buy public homes with still quite a bit of lease.*** However,
when we look at the entire resale housing market, different types of Singaporean households with differing household needs are all put into the mix, and hence, potential patterns of specific Singaporean household profiles get mixed up and doesn't show up. Or this could just be a case of the [Simpson's Paradox](https://en.wikipedia.org/wiki/Simpson%27s_paradox). Just some random thoughts from my side, but still a good thought experiment for a chill weekend.

##### Final Remarks
Data isn’t a silver lining. It helped me identified quite a few interesting patterns, but it doesn’t help me explain why such a pattern is happening. I only want to do so much inferences based on my analysis, but I do want to share what I have seen from the data. Hopefully, some of these analysis is as interesting to some of you guys as they are to me.

As one can tell, I didn't do a very comprehensive analysis on the topic I have at hand. Hence, anyone interested to reach out and have a conversation about this with me ( or anything relating to housing ) can just reach out to me here on **[Linkedin](https://www.linkedin.com/in/cliff-chew-kt/).** If you are interested, do take a look at my other analyses, where I covered some other housing topics like **[million dollar public homes in Singapore](https://sg-housing.onrender.com/blog/posts/sg-mil-public-homes-2024)**. Looking to purchase a resale public home soon? Take a look at my **[simple, free dashboard](https://sg-housing.onrender.com/public-homes)** that shows public homes sold in the past 6 months. Interested in how I look on TV? Watch this **[clip of me on CNA, where I share some interesting public housing data I analysed](https://youtu.be/uu-rkZqNb5A?si=NotogceYNNStvsKn&t=738)** ( or just watch the entire series. It is really interesting ).
