---
date: "2024-08-25"
published: True 
tags:
  - Public Housing
  - Private Housing
title: Comparing Public and Private Home Transactions in Singapore
description: This is what I found after a quick comparison of our public and private housing data!
---

It has been a long while since I wrote a new Medium or SubStack post, 
because I have been busy writing code that enables every Singaporean to look at 
our Singapore public housing market through an analytics lens. While editing the 
dashboards for my HDB data set from data.gov.sg, I have also been playing with the 
private property market data set provided by URA.

After several weeks of on-off data exploration, here are some of patterns I found 
between our private and public housing markets, or at least how URA differs with HDB:

##### Bulk sales exist for private residential homes
**... but never for public homes.** While I was initially confused, speaking to some
domain experts got me to realise this could be some tycoon buying a few private 
homes at one go ( yes, such cases exist ! ) or developers buying up an old estate
to re-develop the entire estate into a new private housing development. This is 
commonly known in Singapore as en-bloc sales. Unfortunately, URA classifies such 
transactions into a single record, **where "noOfUnit > 1", while also having only
a single "nettPrice" value**. While this may be an administrative commonplace, this
does affect how I perform my analyses down the road. **Firstly, I would want to
build a dashboard that allows people ( *who are not private property developers* )
to filter for private home sales in Singapore.** These bulk sales would not provide
a good representation of private home transactions to an individual household,
and the easier way to reflect such bulk sales is to exclude them from my dashboard
search. **I also could divide the nettPrice by the noOfUnits to reflect the 
average price of per unit sold for that en-bloc transaction.** Having the price 
of a single unit sold, even in such en-bloc situations, and may still provide a
better comparison of prices across private and potentially, public residential
homes. That said, I will have to indicate any average prices derived from 
on-bloc sales that are shown on my dashboard, or include an option to drop bulk
sale transactions from the search results.

##### Both URA and HDB provide home sizes in square metres
However, the property marketing collateral I remember seeing shows home sizes 
in square feet instead. Largely, I do feel Singaporeans prefer to think in 
price per square feet, which means I need to convert square metres to square 
feet myself.

##### Zoning used by URA and HDB are different
URA uses a district code and a broader
<a href="https://www.propertyguru.com.sg/property-guides/ccr-ocr-rcr-region-singapore-ura-map-21045" target="_blank">
CCR, RCR and OCR</a> zoning, while HDB uses a residential zoning system. Just a 
quick glance at these zoning systems suggests that they don't match up fully. 
If true ( I have yet to confirm this thoroughly ), this will require more work 
if I want a dashboard that combines both private and public home transactions,
and to allow comparing between private and public home prices by regions. 
I will definitely need to investigate this further.

##### Public Housing is regulated; Private Housing is not ( so ) regulated
**The regulated nature of our public housing market shows up in its price
distributions, especially when comparing with our private property prices.**
While our Singapore public resale homes are getting expensive in recent years,
their box plot price distributions still exhibit visible 25th to 75th
percentile ranges with some outliers.

<iframe src="/static/img/private-public/public-housing.html" width="700" height="580"></iframe>
*Fig 1 - (Above ) Distribution of Singapore public home resale transactions; Taken from 
<a href="https://sg-housing.onrender.com/sg-public-home-trends" target="_blank">
    https://sg-housing.onrender.com/sg-public-home-trends</a>*

**On the other hand, plotting private home price transactions into their respective
box plot distributions shows that their 25th to 75th percentile boxes are barely
visible, while many more outlier price transactions exist too.** This suggests the
very diverse nature of our private housing market, which does span across 
leasehold and freehold units, and across high-rise apartments, penthouses and
huge landed multi-storey bungalows.

<iframe src="/static/img/private-public/overall.html" width="700" height="580"></iframe>
*Fig 2 - ( Above ) Box Plot Distributions of all SG Private Housing Transactions in the last 5 years*

##### Private Property Price Clusters Exist!
**Creating box plot charts by private property house types do allow us to identify
some price clustering within private housing types!** However, apartments and
condominiums still exhibit price distributions that have very short 25th to 
75th percentile with many outliers. **This suggests the wide variety of apartments
and condominiums that exist in Singapore.** This may also suggest the complicated
nature of public home upgraders in choosing the right kind of condominium or
apartment that they hope to upgrade too. Do note that the axes across different
housing types are quite different, so for example, detached homes ( larger 
landed homes ) have price ranges that are much higher than Executive Condominiums.

<iframe src="/static/img/private-public/Apartment.html" width="700" height="580"></iframe>
*Fig 3 - ( Above ) Apartment Price Distributions, with their 25th to 75th percentile being 
barely visible*


<iframe src="/static/img/private-public/Condo.html" width="700" height="580"></iframe>
*Fig 4 - ( Above ) Condo Price Distributions, with their 25th to 75th percentile being
barely visible*

<iframe src="/static/img/private-public/Detached.html" width="700" height="580"></iframe>
*Fig 5 - ( Above ) Detached Home Distributions*


<iframe src="/static/img/private-public/S. Detached.html" width="700" height="580"></iframe>
*Fig 6 - ( Above ) Strata Detached Home Distributions - They most probably have such large
long 25th to 75th percentile boxes due to their lower amount of transactions*

The Strata Detached Home distributions are most probably affected by the their 
low amount of transactions, as I would not expect too many of them to be 
transacted. I am also not too sure what does "Strata" mean, but quite a few 
housing type had "Strata" in them. I would need to research a bit more to see 
if I can just ignore "Strata" and combine several housing types together.

<iframe src="/static/img/private-public/S. Semi-detached.html" width="700" height="580"></iframe>
*Fig 7 - ( Above ) Strata Semi-Detached Home Distributions*

<iframe src="/static/img/private-public/Terrace.html" width="700" height="580"></iframe>
*Fig 8 - ( Above ) Terrace Home Distributions*

<iframe src="/static/img/private-public/Semi-D.html" width="700" height="580"></iframe>
*Fig 9 - ( Above ) Semi-Detached Home Distributions*

<iframe src="/static/img/private-public/S. Terrace.html" width="700" height="580"></iframe>
*Fig 10 - ( Above ) Strata Terrace Home Distributions*

<iframe src="/static/img/private-public/EC.html" width="700" height="580"></iframe>
*Fig 11 - ( Above ) Executive Condo Price Distributions - Don't they look similar to 
the public housing price distributions shown earlier?*

##### About Executive Condominiums ( ECs )
These are public home projects that get to transit to private housing after 10
years from their launch. These units also have a starting tenure of 99 years, 
like most other leasehold residential units in Singapore. And maybe because of
their "humble" origins, their price distributions and movements do seem to 
follow closely to our public housing markets, and are less wide-ranging than 
their apartment and condominium counterparts.

##### Next Steps
This analysis that I am doing here is definitely very basic. Building up with this 
private housing data set, I would love to see if I can find any trends with our 
private housing data, and in particular, how it relates to our public resale 
housing market. However, my first cut would most probably be building a separate 
private housing market dashboard that caters to the quirks of our private housing 
market in Singapore.

Here are some links for those interested to explore more about 
our Singapore housing market:

<ol>
<li>1. <a href="/public-homes" target="_blank">Singapore Public Home Past Transaction Search</a></li>
<li>2. <a href="/public-home-trends" target="_blank">Singapore Public Home Trends</a></li>
<li>3. <a href="/blog" target="_blank">Singapore Public Home Analytics Deep Dives</a></li>
<ol>
<p></p>
