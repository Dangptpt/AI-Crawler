from chatGPT.XpathExtractor import XpathExtractor


extractor = XpathExtractor(
    url = 'https://cafef.vn/giam-doanh-thu-va-tang-chi-phi-quan-ly-saigonres-chuyen-tu-lai-sang-lo-sau-soat-xet-188240904101337278.chn',
    max_retries = 0
)

html = extractor.process()


print("Done!")
