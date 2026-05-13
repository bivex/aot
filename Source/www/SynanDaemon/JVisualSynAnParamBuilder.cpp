#include "JVisualSynAnParamBuilder.h"
#include "synan/SynanLib/SyntaxHolder.h"

struct SGroup
{
public:
	int m_W1;
	int m_W2;
	bool m_IsGroup;
	bool m_IsSubj;
	std::string m_strDescr;
	bool operator < (const SGroup& gr) const {
		if (m_W1 != gr.m_W1) return m_W1 < gr.m_W1;
		return m_W2 < gr.m_W2;
	}

	void ToJson (CJsonObject& o) const {
		o.add_int("start", m_W1);
        o.add_int("last", m_W2);
        o.add_bool("isGroup", m_IsGroup);
        o.add_bool("isSubj", m_IsSubj);
        o.add_string_copy("descr", m_strDescr);
	}

};


struct SSynVariant2Groups
{
public:
	std::vector< CSynUnit> m_SynUnits;
	std::vector<SGroup> m_Groups;

};

class JVisualSynAnParamBuilder
{
	void GetTopClauses(const CSentence& piSent, std::vector<long>& topClauses);
	void AddVariants(std::vector<SSynVariant2Groups>& synVariants, long iClause, const CSentence& piSent);
	void AddOneVariant(std::vector<SSynVariant2Groups>& synVariants, const CMorphVariant& piVar, const CSentence& piSent, const CClause& Clause);
	void AddGroups(std::vector<SSynVariant2Groups>& synVariants, const CMorphVariant& piVar, const CClause& Clause);
	void MultVariants(std::vector<SSynVariant2Groups>& SynVariants1, std::vector<SSynVariant2Groups>& synVariants2);
	void MultTwoVariants(SSynVariant2Groups& var1, SSynVariant2Groups& var2, SSynVariant2Groups& res);
	void AddHomonym(std::vector<SSynVariant2Groups>& synVariants, const CSynUnit& Unit);
	void AddGroup(std::vector<SSynVariant2Groups>& synVariants, const CGroup& piGroup);
    void WriteWords(const CSentence& piSent, long StartWord, long LastWord, CJsonObject& words);
    void WriteVariant(const SSynVariant2Groups& var, CJsonObject& o, const CAgramtab* gramTab);

public:
	const CSyntaxHolder* m_pSyntaxHolder;
	std::vector<std::string> m_OriginalWords;
	std::vector<std::string> m_UpperWords;
	size_t m_OriginalWordIdx;

	void TokenizeOriginal(const std::string& text);
	std::string GetOriginalWord(const std::string& upperWord);

	JVisualSynAnParamBuilder(const CSyntaxHolder* pSyntaxHolder);
	virtual ~JVisualSynAnParamBuilder();
	void BuildJson(const CSentence& piSent, CJsonObject& o);
};

JVisualSynAnParamBuilder::JVisualSynAnParamBuilder(const CSyntaxHolder* pSyntaxHolder)
{
	m_pSyntaxHolder = pSyntaxHolder;
	m_OriginalWordIdx = 0;
}

JVisualSynAnParamBuilder::~JVisualSynAnParamBuilder()
{
}

void JVisualSynAnParamBuilder::TokenizeOriginal(const string& text) {
	m_OriginalWords.clear();
	m_UpperWords.clear();
	m_OriginalWordIdx = 0;
	size_t i = 0;
	while (i < text.size()) {
		unsigned char c = text[i];
		if (c <= 32) {
			i++;
			continue;
		}
		size_t start = i;
		bool isWord = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c > 127 || c == '_' || c == '@' || c == '/';
		if (isWord) {
			while (i < text.size()) {
				unsigned char ch = text[i];
				bool isWordCh = (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9') || ch > 127 || ch == '_' || ch == '\'' || ch == '-' || ch == '/' || ch == '@';
				if (isWordCh)
					i++;
				else if (ch == '.' && i + 1 < text.size() && ((text[i+1] >= 'a' && text[i+1] <= 'z') || (text[i+1] >= 'A' && text[i+1] <= 'Z') || (text[i+1] >= '0' && text[i+1] <= '9')))
					i++;
				else
					break;
			}
		} else {
			i++;
		}
		std::string word = text.substr(start, i - start);
		std::string upper = word;
		MakeUpperUtf8(upper);
		m_OriginalWords.push_back(std::move(word));
		m_UpperWords.push_back(std::move(upper));
	}
}

std::string JVisualSynAnParamBuilder::GetOriginalWord(const std::string& upperWord)
{
	if (m_OriginalWords.empty()) return upperWord;
	size_t startIdx = m_OriginalWordIdx;
	while (m_OriginalWordIdx < m_OriginalWords.size()) {
		if (m_UpperWords[m_OriginalWordIdx] == upperWord)
			return m_OriginalWords[m_OriginalWordIdx];
		m_OriginalWordIdx++;
	}
	if (startIdx > 0) {
		m_OriginalWordIdx = 0;
		while (m_OriginalWordIdx < startIdx) {
			if (m_UpperWords[m_OriginalWordIdx] == upperWord)
				return m_OriginalWords[m_OriginalWordIdx];
			m_OriginalWordIdx++;
		}
		m_OriginalWordIdx = startIdx;
	}
	return upperWord;
}

void JVisualSynAnParamBuilder::WriteWords(const CSentence& piSent, long StartWord, long LastWord, CJsonObject& words)
{
	for(int i = StartWord ; i <= LastWord ; i++ ) {
		const CSynWord& W = piSent.m_Words[i];
        CJsonObject word(words.get_doc());
        word.add_string_copy("str",  GetOriginalWord(W.m_strWord));

        CJsonObject homs(words.get_doc(), rapidjson::kArrayType);
		for(auto& h : W.m_Homonyms)	{
            rapidjson::Value hom;
            hom.SetString(h.GetLemma().c_str(), h.GetLemma().length(), words.get_allocator());
            homs.push_back(hom);
        }
        word.move_to_member("homonyms", homs.get_value());
		words.push_back(word);
	}

}

void JVisualSynAnParamBuilder::GetTopClauses(const CSentence& piSent, std::vector<long>& topClauses)
{
	long clCount = piSent.m_Clauses.size();
	const CClause*  piNextClause = 0;

	for(long i = piSent.m_Clauses.size() - 1 ; i >= 0 ; i-- )
	{
		const CClause* piClause = &piSent.m_Clauses[i];

		if( (piNextClause == NULL) || (piNextClause->m_iFirstWord == piClause->m_iLastWord + 1 ) )
		{
			piNextClause = piClause;
			topClauses.push_back(i);
		}
	}
	reverse(topClauses.begin(), topClauses.end());
}

void JVisualSynAnParamBuilder::AddVariants(std::vector<SSynVariant2Groups>& allSynVariants,long iClause,  const CSentence& piSent)
{
	const CClause& Clause = piSent.m_Clauses[iClause];

	for(CSVI i =  Clause.m_SynVariants.begin() ; i != Clause.m_SynVariants.end(); i++ )
	{
		std::vector<SSynVariant2Groups> synVariants;
		AddOneVariant(synVariants, *i, piSent, Clause);

		for( int j = 0 ; j < synVariants.size() ; j++ )
		{
			SGroup group;
			group.m_W1 = Clause.m_iFirstWord;
			group.m_W2 = Clause.m_iLastWord;
			group.m_IsGroup = false;
			group.m_IsSubj = false;
			group.m_strDescr = m_pSyntaxHolder->GetClauseTypeDescr(Clause,  i->m_ClauseTypeNo);
			MakeLowerUtf8(group.m_strDescr);
			synVariants[j].m_Groups.push_back(group);
		}

		allSynVariants.insert(allSynVariants.end(), std::make_move_iterator(synVariants.begin()), std::make_move_iterator(synVariants.end()));
	}
}

void JVisualSynAnParamBuilder::AddHomonym(std::vector<SSynVariant2Groups>& synVariants, const CSynUnit& Unit)
{
	for (auto& v: synVariants) {
		v.m_SynUnits.push_back(Unit);
	}
}

void JVisualSynAnParamBuilder::AddGroup(std::vector<SSynVariant2Groups>& synVariants, const CGroup&  piGroup)
{
	for (auto& v : synVariants)	{
		SGroup group;
		group.m_W1 = piGroup.m_iFirstWord;
		group.m_W2 = piGroup.m_iLastWord;
		group.m_IsGroup = true;
		group.m_IsSubj = false;
		group.m_strDescr = m_pSyntaxHolder->m_Synan.GetOpt()->GetGroupNameByIndex(piGroup.m_GroupType);
		MakeLowerUtf8(group.m_strDescr);
		v.m_Groups.push_back(group);
	}
}


void JVisualSynAnParamBuilder::AddGroups(std::vector<SSynVariant2Groups>& synVariants, const CMorphVariant& piVar, const CClause& Clause) {
	for (long i = 0; i < piVar.m_vectorGroups.GetGroups().size(); i++) {
		AddGroup(synVariants, piVar.m_vectorGroups.GetGroups()[i]);
	}

	long iSubj = piVar.GetFirstSubject();
	long iPred = piVar.m_iPredk;
	if ((iSubj >= 0) && (iPred >= 0))
	{
		iSubj = piVar.GetSentenceCoordinates(iSubj).m_iFirstWord;
		iPred = piVar.GetSentenceCoordinates(iPred).m_iFirstWord;
		for (auto& v : synVariants) {
			SGroup group;
			group.m_W1 = iSubj;
			group.m_W2 = iPred;
			group.m_strDescr = "sp";
			group.m_IsSubj = true;
			group.m_IsGroup = false;
			v.m_Groups.push_back(group);
		}
	}

}


void JVisualSynAnParamBuilder::AddOneVariant(std::vector<SSynVariant2Groups>& allSynVariants,const CMorphVariant& piVar,  const CSentence& piSent, const CClause& Clause)
{
	long unitsCount = piVar.m_SynUnits.size();
	SSynVariant2Groups var;
	allSynVariants.push_back(std::move(var));

	for(long i = 0 ; i < unitsCount ; i++ )
	{
		if( piVar.m_SynUnits[i].m_Type == EWord)
		{
			AddHomonym(allSynVariants, piVar.m_SynUnits[i]);
		}
		else
		{
			std::vector<SSynVariant2Groups> synVariants;
			int ClauseNo = piSent.FindClauseIndexByPeriod(piVar.m_SynUnits[i].m_SentPeriod);
			AddVariants(synVariants, ClauseNo, piSent);
			MultVariants(allSynVariants, synVariants);
		}
	}

	AddGroups(allSynVariants, piVar, Clause);
}

void JVisualSynAnParamBuilder::MultTwoVariants(SSynVariant2Groups& var1, SSynVariant2Groups& var2, SSynVariant2Groups& res)
{
	res = std::move(var1);
	res.m_SynUnits.insert(res.m_SynUnits.end(),
		std::make_move_iterator(var2.m_SynUnits.begin()),
		std::make_move_iterator(var2.m_SynUnits.end()));
	res.m_Groups.insert(res.m_Groups.end(),
		std::make_move_iterator(var2.m_Groups.begin()),
		std::make_move_iterator(var2.m_Groups.end()));
}


void JVisualSynAnParamBuilder::MultVariants(std::vector<SSynVariant2Groups>& synVariants1, std::vector<SSynVariant2Groups>& synVariants2)
{
	size_t s1 = synVariants1.size();
	size_t s2 = synVariants2.size();

	if (s1 == 0) {
		synVariants1 = std::move(synVariants2);
		return;
	}

	std::vector<SSynVariant2Groups> resVars;
	resVars.reserve(s1 * s2);
	for(size_t i = 0 ; i < s1 ; i++)
	{
		for(size_t j = 0 ; j < s2 ; j++)
		{
			SSynVariant2Groups res;
			MultTwoVariants(synVariants1[i], synVariants2[j], res);
			resVars.push_back(std::move(res));
		}
	}

	synVariants1 = std::move(resVars);
}

void JVisualSynAnParamBuilder::WriteVariant(const SSynVariant2Groups& var, CJsonObject& o, const CAgramtab* gramTab) {

    CJsonObject units(o.get_doc(), rapidjson::kArrayType);
	for(const auto& u : var.m_SynUnits) {
        CJsonObject unit(o.get_doc());
		unit.add_int("homNo",  u.m_iHomonymNum);
		std::string grm = u.GetPartOfSpeechStr();
		grm += ' ';
		grm += gramTab->GrammemsToStr(u.m_iGrammems);
		unit.add_string_copy("grm", grm);
		units.push_back(unit.get_value());
	}
    o.move_to_member("units", units.get_value());

    CJsonObject groups(o.get_doc(), rapidjson::kArrayType);
	for (const auto& group : var.m_Groups) {
        CJsonObject g(o.get_doc());
		group.ToJson(g);
        groups.push_back(g.get_value());
	}
    o.move_to_member("groups", groups.get_value());
}

void JVisualSynAnParamBuilder::BuildJson(const CSentence& piSent, CJsonObject& o) {
    std::vector<long> topClauses;
    GetTopClauses(piSent, topClauses);

    auto* gramTab = GetMHolder(m_pSyntaxHolder->m_LemText.GetDictLanguage()).m_pGramTab;

    for(long i = 0; i < topClauses.size() ; i++ ) {
        const CClause& C = 	piSent.m_Clauses[topClauses[i]];
        CJsonObject clause(o.get_doc());
        CJsonObject words(o.get_doc(), rapidjson::kArrayType);
        WriteWords(piSent, C.m_iFirstWord, C.m_iLastWord, words);
        clause.move_to_member("words",  words.get_value());

        std::vector<SSynVariant2Groups> synVariants;
        AddVariants(synVariants, topClauses[i],  piSent);
        CJsonObject variants(o.get_doc(), rapidjson::kArrayType);
        int offset = C.m_iFirstWord;
        for(auto& v : synVariants) {
            for(auto& g : v.m_Groups)	{
                g.m_W1 -= offset;
                g.m_W2 -= offset;
            };
            sort(v.m_Groups.begin(), v.m_Groups.end());
            CJsonObject var(o.get_doc());
            WriteVariant(v, var, gramTab);
            variants.push_back(var.get_value());
        }
        clause.move_to_member("variants", variants.get_value());
        o.push_back(clause.get_value());
    }
}

std::string BuildJson(CSyntaxHolder* pSyntaxHolder, const std::string& query, const std::string& originalQuery) {
	JVisualSynAnParamBuilder builder(pSyntaxHolder);
	if (!originalQuery.empty()) {
		builder.TokenizeOriginal(originalQuery);
	}
    rapidjson::Document d;
    CJsonObject sents(d, rapidjson::kArrayType);
	for (auto& s : pSyntaxHolder->m_Synan.m_vectorSents) {
        CJsonObject o(d, rapidjson::kArrayType);
        builder.BuildJson(*s, o);
        sents.push_back(o.get_value());
	}
	return sents.dump_rapidjson();
}
